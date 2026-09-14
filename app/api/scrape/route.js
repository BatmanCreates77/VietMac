/**
 * API Route: /api/scrape
 * Manual/dev-trigger for the MacBook price scraper. NOT wired to any
 * production schedule — the real automation is a local launchd job
 * (macbook_scraper/com.vietmac.price-update.plist) that runs Python +
 * a real browser directly on a machine that has them installed, then
 * commits + pushes the result. Vercel's serverless runtime has neither
 * Python nor browser binaries, so this route can never actually
 * succeed when called in production; it exists for local dev only.
 *
 * Usage:
 * - Local dev: GET/POST to /api/scrape with `Authorization: Bearer <CRON_SECRET>`
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

const execAsync = promisify(exec);

export const dynamic = 'force-dynamic';
export const maxDuration = 300; // 5 minutes max execution time

export async function GET(request) {
  return handleScrape(request);
}

export async function POST(request) {
  return handleScrape(request);
}

async function handleScrape(request) {
  const startTime = Date.now();

  try {
    // Fail closed: this endpoint requires CRON_SECRET to be configured.
    // It used to fail OPEN (no auth check at all) when the env var was
    // unset, meaning any unauthenticated caller could trigger a scraper
    // run — harmless on Vercel today only because Python isn't present
    // there, but that's an accident of environment, not a real control.
    const authHeader = request.headers.get('authorization');
    const cronSecret = process.env.CRON_SECRET;

    if (!cronSecret) {
      return NextResponse.json(
        { error: 'Scrape trigger not configured (CRON_SECRET unset)' },
        { status: 503 }
      );
    }

    if (authHeader !== `Bearer ${cronSecret}`) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    console.log('🚀 Starting price scraper...');

    // Path to scraper script
    const scraperPath = path.join(process.cwd(), 'macbook_scraper');
    const scriptPath = path.join(scraperPath, 'update_prices.py');

    // Check if Python is available
    let pythonCmd = 'python3';
    try {
      await execAsync('which python3');
    } catch {
      try {
        await execAsync('which python');
        pythonCmd = 'python';
      } catch {
        throw new Error('Python not found. Please install Python 3.');
      }
    }

    // Run the scraper
    console.log(`📊 Executing: ${pythonCmd} ${scriptPath}`);
    const { stdout, stderr } = await execAsync(
      `cd ${scraperPath} && ${pythonCmd} update_prices.py`,
      {
        timeout: 280000, // 4 min 40 sec timeout
        maxBuffer: 10 * 1024 * 1024 // 10MB buffer for output
      }
    );

    // Check if output file was updated
    const outputPath = path.join(scraperPath, 'output', 'latest_products.json');
    let productsData = null;
    let fileStats = null;

    try {
      const fileContent = await fs.readFile(outputPath, 'utf-8');
      productsData = JSON.parse(fileContent);
      fileStats = await fs.stat(outputPath);
    } catch (error) {
      console.error('Error reading output file:', error);
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    console.log('✅ Scraper completed successfully');
    console.log(stdout);
    if (stderr) {
      console.warn('Scraper stderr:', stderr);
    }

    return NextResponse.json({
      success: true,
      message: 'Price scraper completed successfully',
      timestamp: new Date().toISOString(),
      duration: `${duration}s`,
      summary: productsData?.summary || null,
      fileUpdated: fileStats ? new Date(fileStats.mtime).toISOString() : null,
      output: {
        stdout: stdout.split('\n').slice(-20).join('\n'), // Last 20 lines
        stderr: stderr || null
      }
    });

  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    console.error('❌ Scraper failed:', error);

    return NextResponse.json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      duration: `${duration}s`,
      details: error.stderr || error.stdout || null
    }, {
      status: 500
    });
  }
}
