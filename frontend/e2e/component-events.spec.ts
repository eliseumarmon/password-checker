import { expect, test } from '@playwright/test';

test('connects welcome and settings actions to session dialogs and file import', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir sesión cifrada anterior' }).click();
  const dialog = page.getByRole('dialog', { name: 'Sesión cifrada' });
  await expect(dialog.getByRole('heading', { name: 'Abrir sesión anterior' })).toBeVisible();
  await dialog.getByRole('button', { name: 'Cancelar' }).click();

  const dataTransfer = await page.evaluateHandle(() => {
    const transfer = new DataTransfer();
    transfer.items.add(new File([
      'name,url,username,password,note\nExample,https://example.invalid/,alice,fake-password-123456,',
    ], 'example.csv', { type: 'text/csv' }));
    return transfer;
  });
  await page.locator('.dropzone').dispatchEvent('drop', { dataTransfer });
  await expect(page.getByRole('button', { name: 'Todas (1)' })).toBeVisible();

  await page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: 'Ajustes' }).click();
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(dialog.getByRole('heading', { name: 'Guardar sesión cifrada' })).toBeVisible();
  await dialog.getByRole('button', { name: 'Cancelar' }).click();
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  await expect(dialog.getByRole('heading', { name: 'Abrir sesión anterior' })).toBeVisible();
});
