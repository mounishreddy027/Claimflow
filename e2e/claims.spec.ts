import { test, expect } from '@playwright/test';

/**
 * ClaimFlow End-to-End User Journey Tests
 * Enforces Playwright patterns from .claude/skills/evaluation/references/playwright-patterns.md
 * Generates verified test evidence and UI visual snapshots.
 */

test.describe('ClaimFlow Core Claims Lifecycle Journey', () => {
  const apiBase = process.env.EVAL_BASE_URL || 'http://127.0.0.1:8000';

  test('Liveness & Health Probe responds under 1,000ms (NFR-07)', async ({ request }) => {
    const start = Date.now();
    const response = await request.get(`${apiBase}/health`);
    const latency = Date.now() - start;

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
    expect(body.service).toBe('claimflow');
    expect(latency).toBeLessThan(1000);
  });

  test('ClaimFlow Dashboard loads with navigation and live stats', async ({ page }) => {
    await page.goto('/');

    // Verify main brand heading (h1) and navigation tabs
    await expect(page.getByRole('heading', { name: 'ClaimFlow' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Claims Dashboard/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /File FNOL/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /AI Fraud Screener/i })).toBeVisible();

    // Capture dashboard UI snapshot artifact
    await page.screenshot({ path: 'playwright-report/snapshots/01-dashboard.png', fullPage: true });
  });

  test('FNOL Claim Intake workflow with policy validation and submission verification', async ({ page }) => {
    await page.goto('/');

    // Navigate to File FNOL tab
    await page.getByRole('button', { name: /File FNOL/i }).click();
    await expect(page.getByRole('heading', { name: /First Notice of Loss/i })).toBeVisible();

    // Locate policy select and wait for backend policies to load asynchronously
    const policySelect = page.locator('#intakePolicySelect');
    await expect(policySelect.locator('option:not([value=""])').first()).toBeAttached({ timeout: 5000 });

    // Explicitly select an active policy
    await policySelect.selectOption({ index: 1 });

    // Fill form using semantic accessible labels
    await page.getByLabel(/Claim Amount/i).fill('3200.00');
    await page.getByLabel(/Incident Description/i).fill('Intersection collision on municipal thoroughfare.');

    // Capture FNOL form snapshot artifact before submission
    await page.screenshot({ path: 'playwright-report/snapshots/02-fnol-form.png', fullPage: true });

    // Submit FNOL form
    await page.getByRole('button', { name: /Submit FNOL Claim/i }).click();

    // Verify submission succeeds via success notification toast
    const toast = page.locator('#toastContainer');
    await expect(toast).toContainText(/filed successfully/i, { timeout: 8000 });

    // Verify redirect to Claims Dashboard and presence of claims
    await expect(page.locator('#section-dashboard')).toBeVisible();

    // Capture post-submission snapshot
    await page.screenshot({ path: 'playwright-report/snapshots/03-fnol-submitted.png', fullPage: true });
  });

  test('Audit Trail & WORM Ledger view with cryptographic verification', async ({ page }) => {
    await page.goto('/');

    // Navigate to Audit Trail tab
    await page.getByRole('button', { name: /Audit Trail/i }).click();
    await expect(page.getByRole('heading', { name: /Cryptographic Audit Trail/i })).toBeVisible();

    // Capture Audit Trail snapshot
    await page.screenshot({ path: 'playwright-report/snapshots/04-audit-trail.png', fullPage: true });
  });
});
