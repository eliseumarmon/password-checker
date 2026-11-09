import { readFile } from 'node:fs/promises';
import { expect, test, type Locator, type Page } from '@playwright/test';
import { welcomeTest } from './isolated-welcome';

// Fictional credentials and TOTP URIs only, built in memory.
const IMPORTED_TOTP = 'otpauth://totp/Example:alice?secret=FICTIONALIMPORTED&issuer=Example';
const EDITED_TOTP = 'otpauth://totp/Example:alice?secret=FICTIONALEDITED&issuer=Example';
const SAFARI_CSV = [
  'Title,URL,Username,Password,Notes,OTPAuth',
  `Example,https://example.invalid/,alice,fictional-Pw-123,,${IMPORTED_TOTP}`,
  'Other,https://other.invalid/,bob,fictional-Pw-456,,',
].join('\n');

async function importSafari(page: Page): Promise<void> {
  // The E2E backend is shared between tests, so importing may replace the previous test's data.
  const replacing = (await (await page.request.get('/api/workspace')).json()).stats.total > 0;
  await page.goto('/');
  await page.locator('input[type=file][accept*=".csv"]').first()
    .setInputFiles([{ name: 'Passwords.csv', mimeType: 'text/csv', buffer: Buffer.from(SAFARI_CSV) }]);
  if (replacing) await confirmWith(page, 'Importar');
  await page.getByRole('tab', { name: 'Todas (2)' }).click();
}

async function confirmWith(page: Page, label: string): Promise<void> {
  const dialog = page.getByRole('alertdialog', { name: 'Confirmar acción' });
  await dialog.getByRole('button', { name: label, exact: true }).click();
  await expect(dialog).toBeHidden();
}

async function openEditor(page: Page, user: string): Promise<Locator> {
  await page.locator('.desktop-table').getByRole('row', { name: new RegExp(user) }).getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor).toBeVisible();
  return editor;
}

function passwordField(editor: Locator): Locator {
  // The other new-password field of the editor; the TOTP field is told apart by its own name.
  return editor.locator('input[autocomplete="new-password"]:not([aria-label="Código 2FA (TOTP)"])');
}

function totpField(editor: Locator): Locator {
  return editor.getByLabel('Código 2FA (TOTP)', { exact: true });
}

test('keeps the Safari TOTP hidden, editable and intact up to the Bitwarden export', async ({ page }) => {
  await importSafari(page);
  // The secret stays out of the general view.
  await expect(page.locator('body')).not.toContainText('FICTIONAL');

  let editor = await openEditor(page, 'alice');
  const totp = totpField(editor);
  const password = passwordField(editor);
  await expect(totp).toHaveAttribute('type', 'password');
  await expect(totp).toHaveValue(IMPORTED_TOTP);
  // Browsers and password managers must not fill a saved site password into the 2FA secret.
  await expect(totp).toHaveAttribute('autocomplete', 'new-password');
  for (const optOut of ['data-1p-ignore', 'data-lpignore', 'data-bwignore']) {
    await expect(totp).toHaveAttribute(optOut);
  }
  // Each secret has its own visibility control.
  await editor.getByRole('button', { name: 'Mostrar contraseña' }).click();
  await expect(password).toHaveAttribute('type', 'text');
  await expect(totp).toHaveAttribute('type', 'password');
  await editor.getByRole('button', { name: 'Mostrar código 2FA' }).click();
  await expect(totp).toHaveAttribute('type', 'text');
  await editor.getByRole('button', { name: 'Ocultar contraseña' }).click();
  await expect(password).toHaveAttribute('type', 'password');
  await expect(totp).toHaveAttribute('type', 'text');

  await totp.fill(EDITED_TOTP);
  await expect(password).toHaveValue('fictional-Pw-123');
  await editor.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(editor).toBeHidden();

  // Reopened: the edit persisted, the password did not change and the field is hidden again.
  editor = await openEditor(page, 'alice');
  await expect(totpField(editor)).toHaveValue(EDITED_TOTP);
  await expect(totpField(editor)).toHaveAttribute('type', 'password');
  await expect(passwordField(editor)).toHaveValue('fictional-Pw-123');
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  editor = await openEditor(page, 'bob');
  await expect(totpField(editor)).toHaveValue('');
  await editor.getByRole('button', { name: 'Cancelar' }).click();

  // Encrypted session round trip.
  const passphrase = 'fictional-session-passphrase';
  await page.getByRole('button', { name: 'Guardar sesión cifrada' }).click();
  const saveDialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await saveDialog.getByLabel(/Contraseña de sesión/).fill(passphrase);
  await saveDialog.getByLabel('Confirmar contraseña').fill(passphrase);
  const download = page.waitForEvent('download');
  await saveDialog.getByRole('button', { name: 'Descargar archivo cifrado' }).click();
  const saved = await download;
  const session = { name: saved.suggestedFilename(), mimeType: 'application/octet-stream', buffer: await readFile(await saved.path()) };
  expect(session.buffer.toString('latin1')).not.toContain('FICTIONAL');
  await expect(saveDialog).toBeHidden();
  await page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: /Ajustes/ }).click();
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  const loadDialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await loadDialog.getByLabel('Archivo cifrado').setInputFiles(session);
  await loadDialog.getByLabel(/Contraseña de sesión/).fill(passphrase);
  await loadDialog.getByRole('button', { name: 'Abrir sesión' }).click();
  await confirmWith(page, 'Abrir sesión');
  await expect(loadDialog).toBeHidden();
  await page.getByRole('tab', { name: 'Todas (2)' }).click();
  editor = await openEditor(page, 'alice');
  await expect(totpField(editor)).toHaveValue(EDITED_TOTP);
  await editor.getByRole('button', { name: 'Cancelar' }).click();

  // The export carries the last value.
  const exported = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar Bitwarden' }).click();
  await confirmWith(page, 'Generar CSV');
  const csv = await readFile(await (await exported).path(), 'utf-8');
  const rows = csv.replace(/^﻿/, '').trim().split('\n');
  expect(rows[0].split(',').at(-1)).toBe('login_totp');
  expect(rows.find(row => row.includes(',alice,'))?.endsWith(`,${EDITED_TOTP}`)).toBe(true);
  expect(rows.find(row => row.includes(',bob,'))?.endsWith(',')).toBe(true);
});

test('asks before discarding an unsaved TOTP edit and keeps the saved one', async ({ page }) => {
  await importSafari(page);
  let editor = await openEditor(page, 'alice');
  await totpField(editor).fill(EDITED_TOTP);
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  await confirmWith(page, 'Descartar cambios');
  await expect(editor).toBeHidden();
  editor = await openEditor(page, 'alice');
  await expect(totpField(editor)).toHaveValue(IMPORTED_TOTP);
});

welcomeTest('lists Safari among the supported exports on the welcome screen', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Arrastra varios CSV de Chrome, Brave, Firefox y Safari.', { exact: false })).toBeVisible();
});
