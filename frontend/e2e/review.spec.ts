import { expect, test, type Locator, type Page } from '@playwright/test';

// Fictional credentials only, built in memory: real exports never touch the repo.
const CHROME_CSV = [
  'name,url,username,password,note',
  'Example,https://example.invalid/login,alice,fake-Shared-123456,first',
  'Example,https://example.invalid/login,alice,fake-Shared-123456,second',
  'Conflict,https://conflict.invalid/,bob,fake-One-1234567,',
  'Conflict,https://conflict.invalid/,bob,fake-Two-1234567,',
].join('\n');
const BRAVE_CSV = [
  'name,url,username,password,note',
  ',android://SIGN@com.example.app/,eve,fake-App-1234567,',
  'Weak,https://weak.invalid/,carol,fake-123,',
].join('\n');

async function importFixtures(page: Page) {
  page.on('dialog', dialog => dialog.accept());
  await page.goto('/');
  await page.locator('input[type=file][accept*=".csv"]').first().setInputFiles([
    { name: 'chrome.csv', mimeType: 'text/csv', buffer: Buffer.from(CHROME_CSV) },
    { name: 'brave.csv', mimeType: 'text/csv', buffer: Buffer.from(BRAVE_CSV) },
  ]);
  await expect(page.getByRole('button', { name: 'Todas (6)' })).toBeVisible();
}

function metric(page: Page, label: string): Locator {
  return page.locator('.metric', { hasText: label }).locator('strong');
}

// WCAG 2.x contrast ratio between the text and its first opaque ancestor background.
function contrastOf(cell: Locator): Promise<number> {
  return cell.evaluate(element => {
    const rgb = (value: string) => (value.match(/[\d.]+/g) ?? []).map(Number);
    const luminance = ([r, g, b]: number[]) => {
      const channel = (c: number) => {
        const s = c / 255;
        return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
    };
    let node: Element | null = element;
    let background = 'rgb(255, 255, 255)';
    while (node) {
      const color = getComputedStyle(node).backgroundColor;
      const alpha = rgb(color)[3];
      if (color !== 'transparent' && (alpha === undefined || alpha > 0)) {
        background = color;
        break;
      }
      node = node.parentElement;
    }
    const [light, dark] = [luminance(rgb(getComputedStyle(element).color)), luminance(rgb(background))]
      .sort((a, b) => b - a);
    return (light + 0.05) / (dark + 0.05);
  });
}

test.beforeEach(async ({ page }) => importFixtures(page));

test('imports several CSV files and groups duplicates and conflicts', async ({ page }) => {
  await expect(metric(page, 'Credenciales')).toHaveText('6');
  await expect(page.getByRole('button', { name: 'Duplicados (2)' })).toBeVisible();
  const table = page.locator('.desktop-table');
  await expect(table.getByRole('row', { name: /Conflict/ })).toBeVisible();
  await expect(table.getByRole('row', { name: /Example/ })).toBeVisible();
});

test('shows Android apps in Bitwarden format', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  const row = page.locator('.desktop-table').getByRole('row', { name: /com\.example\.app/ });
  await expect(row).toContainText('androidapp://com.example.app');
  await expect(row).toContainText('Android');
});

test('keeps table cells readable on the dark theme', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  const row = page.locator('.desktop-table tbody tr').first();
  for (const index of [1, 2, 3, 5]) {
    expect(await contrastOf(row.locator('td').nth(index))).toBeGreaterThanOrEqual(4.5);
  }
});

test('keeps drawer actions visible and saves edits', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 600 });
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /bob/ }).first()
    .getByRole('button', { name: 'Editar' }).click();
  const drawer = page.getByRole('dialog', { name: 'Editar credencial' });
  const save = drawer.getByRole('button', { name: 'Guardar cambios' });
  await expect(save).toBeInViewport();
  await expect(drawer.getByRole('button', { name: 'Cancelar' })).toBeInViewport();

  await drawer.getByLabel('Nombre').fill('Conflict renamed');
  await save.click();
  await expect(drawer).toBeHidden();
  await expect(page.locator('.desktop-table')).toContainText('Conflict renamed');
});

test('merges exact copies into the trash and can undo it', async ({ page }) => {
  await page.getByRole('button', { name: 'Fusionar copias exactas' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('1');
  await expect(page.getByRole('button', { name: 'Todas (5)' })).toBeVisible();
  await page.getByRole('button', { name: /Deshacer/ }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
});

function sidebar(page: Page): Locator {
  return page.getByRole('complementary', { name: 'Navegación principal' });
}

test('trashes a row from its quick action and restores it from the trash', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /carol/ })
    .getByRole('button', { name: 'Mover a la papelera' }).click();
  await expect(page.getByRole('button', { name: 'Todas (5)' })).toBeVisible();
  await expect(page.locator('.desktop-table')).not.toContainText('carol');

  await sidebar(page).getByRole('button', { name: /Papelera/ }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Papelera');
  const row = page.locator('.desktop-table').getByRole('row', { name: /carol/ });
  await row.getByRole('button', { name: 'Restaurar' }).click();
  await expect(page.getByText('La papelera está vacía.')).toBeVisible();
  await expect(metric(page, 'En la papelera')).toHaveText('0');
});

test('discards a record from the editor into the trash', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /carol/ })
    .getByRole('button', { name: 'Editar' }).click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor.getByRole('checkbox')).toHaveCount(0);
  await editor.getByRole('button', { name: 'Descartar' }).click();
  await expect(editor).toBeHidden();
  await expect(metric(page, 'En la papelera')).toHaveText('1');
});

test('reviews a record from the audit without leaving the audit', async ({ page }) => {
  await page.getByRole('complementary', { name: 'Navegación principal' }).getByRole('button', { name: /Auditoría/ }).click();
  await page.locator('.audit-block', { hasText: 'Contraseñas poco seguras' }).getByRole('button', { name: 'Revisar' }).first().click();
  const editor = page.getByRole('dialog', { name: 'Editar credencial' });
  await expect(editor).toBeVisible();
  await editor.getByRole('button', { name: 'Cancelar' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Auditoría local');
});

test('opens the editor centred on the screen', async ({ page }) => {
  await page.getByRole('button', { name: 'Todas (6)' }).click();
  await page.locator('.desktop-table').getByRole('row', { name: /carol/ })
    .getByRole('button', { name: 'Editar' }).click();
  const box = await page.getByRole('dialog', { name: 'Editar credencial' }).boundingBox();
  const viewport = page.viewportSize()!;
  expect(Math.abs(box!.x + box!.width / 2 - viewport.width / 2)).toBeLessThan(10);
});

test('uses compact cards and rows and normal-sized checkboxes', async ({ page }) => {
  for (const card of await page.locator('.metric').all()) {
    expect((await card.boundingBox())!.height).toBeLessThanOrEqual(76);
  }
  const row = (await page.locator('.desktop-table tbody tr').first().boundingBox())!;
  expect(row.height).toBeLessThanOrEqual(56);
  const checkbox = (await page.getByRole('checkbox', { name: 'Solo pendientes' }).boundingBox())!;
  expect(Math.max(checkbox.width, checkbox.height)).toBeLessThanOrEqual(20);
});

test('collapses the sidebar to icons and remembers it', async ({ page }) => {
  const aside = sidebar(page);
  const width = async () => (await aside.boundingBox())!.width;
  await aside.getByRole('button', { name: 'Contraer menú' }).click();
  await expect.poll(width).toBeLessThanOrEqual(72);
  await aside.getByRole('button', { name: /Auditoría/ }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Auditoría local');

  await page.reload();
  await expect.poll(width).toBeLessThanOrEqual(72);
  await aside.getByRole('button', { name: 'Expandir menú' }).click();
  await expect.poll(width).toBeGreaterThan(200);
});

test('shows only cards, not the table, on narrow screens', async ({ page }) => {
  await page.setViewportSize({ width: 600, height: 800 });
  await expect(page.locator('.desktop-table')).toBeHidden();
  await expect(page.locator('.mobile-cards .record-card').first()).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Navegación móvil' })).toBeVisible();
});

test('trashes a whole duplicate group from its row actions', async ({ page }) => {
  const table = page.locator('.desktop-table');
  await expect(table.getByRole('columnheader', { name: 'Acciones' })).toBeVisible();
  await table.getByRole('row', { name: /Conflict/ }).getByRole('button', { name: 'Mover grupo a la papelera' }).click();
  await expect(metric(page, 'En la papelera')).toHaveText('2');
  await expect(page.getByRole('button', { name: 'Duplicados (1)' })).toBeVisible();
});
