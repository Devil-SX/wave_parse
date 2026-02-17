import { test, expect } from '@playwright/test';

test.describe('Benchmark Web Page', () => {
  test('page loads with correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/VCD\/FST/);
  });

  test('all sections are visible', async ({ page }) => {
    await page.goto('/');
    const sections = ['#formats', '#overview', '#methodology', '#results', '#analysis', '#conclusions'];
    for (const id of sections) {
      await expect(page.locator(id)).toBeVisible();
    }
  });

  test('charts render with non-zero dimensions', async ({ page }) => {
    await page.goto('/');
    // Wait for Chart.js to render
    await page.waitForTimeout(1000);
    const canvases = page.locator('canvas');
    const count = await canvases.count();
    expect(count).toBeGreaterThanOrEqual(2);
    for (let i = 0; i < count; i++) {
      const box = await canvases.nth(i).boundingBox();
      expect(box).not.toBeNull();
      expect(box!.width).toBeGreaterThan(0);
      expect(box!.height).toBeGreaterThan(0);
    }
  });

  test('library comparison table displayed', async ({ page }) => {
    await page.goto('/');
    // v2 uses a comparison table instead of cards
    const rows = page.locator('#libCompareTable tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(8);
  });

  test('scale selector switches data', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(500);
    // Click medium scale
    await page.click('[data-scale="medium"]');
    await page.waitForTimeout(500);
    // The active button should change
    await expect(page.locator('[data-scale="medium"]')).toHaveClass(/active/);
    await expect(page.locator('[data-scale="large"]')).not.toHaveClass(/active/);
  });

  test('format toggle switches between VCD and FST', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(500);
    // VCD should be active by default
    await expect(page.locator('[data-fmt="vcd"]')).toHaveClass(/active/);
    // Click FST
    await page.click('[data-fmt="fst"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-fmt="fst"]')).toHaveClass(/active/);
    await expect(page.locator('[data-fmt="vcd"]')).not.toHaveClass(/active/);
  });
});

test.describe('Screenshots', () => {
  test('desktop full page screenshot', async ({ page, browserName }, testInfo) => {
    test.skip(testInfo.project.name === 'mobile', 'desktop only');
    await page.goto('/');
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: 'docs/screenshots/desktop-full.png',
      fullPage: true
    });
  });

  test('mobile full page screenshot', async ({ page, browserName }, testInfo) => {
    test.skip(testInfo.project.name === 'desktop', 'mobile only');
    await page.goto('/');
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: 'docs/screenshots/mobile-full.png',
      fullPage: true
    });
  });

  test('charts section screenshot', async ({ page, browserName }, testInfo) => {
    test.skip(testInfo.project.name === 'mobile', 'desktop only');
    await page.goto('/');
    await page.waitForTimeout(1500);
    const resultsSection = page.locator('#results');
    await resultsSection.screenshot({
      path: 'docs/screenshots/charts-section.png'
    });
  });
});
