#!/usr/bin/env python3
"""
Iran War Carousel — Instagram PNG Exporter
Uses Playwright (headless Chromium) to render each slide at 1080×1080px.

Usage:
    python export_carousel.py

Output:
    ./output/slide_01.png ... slide_07.png  (1080×1080, Instagram-ready)
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

HTML_FILE = Path(__file__).parent / "iran_carousel_v2.html"
OUTPUT_DIR = Path(__file__).parent / "output"
SLIDE_COUNT = 5
SIZE = 1080  # Instagram square


async def export_slides():
    OUTPUT_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        # Load the HTML — set scale to 1.0 for full 1080px render
        html_path = HTML_FILE.resolve().as_uri()
        await page.goto(html_path, wait_until="networkidle")

        # Override CSS scale to 1 so slides render at full 1080px
        await page.evaluate("""() => {
            document.documentElement.style.setProperty('--scale', '1');
            const viewport = document.querySelector('.viewport');
            if (viewport) {
                viewport.style.width = '1080px';
                viewport.style.height = '1080px';
            }
            const wrap = document.querySelector('.carousel-wrap');
            if (wrap) {
                wrap.style.width = '1080px';
            }
            // Hide nav chrome
            document.querySelector('.nav').style.display = 'none';
            document.querySelector('.slide-counter').style.display = 'none';
            document.querySelector('.hint').style.display = 'none';
        }""")

        # Wait for Google Fonts
        await page.wait_for_timeout(1500)

        for i in range(SLIDE_COUNT):
            # Navigate to slide i
            await page.evaluate(f"go({i})")
            await page.wait_for_timeout(200)

            # Screenshot the viewport div only
            slide_el = page.locator(".viewport")
            out_path = OUTPUT_DIR / f"slide_{i+1:02d}.png"
            await slide_el.screenshot(path=str(out_path))
            print(f"  ✓ slide_{i+1:02d}.png saved")

        await browser.close()

    print(f"\nDone — {SLIDE_COUNT} slides in ./{OUTPUT_DIR.name}/")


if __name__ == "__main__":
    # Check playwright is installed
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Installing playwright...")
        os.system("pip install playwright && playwright install chromium")

    asyncio.run(export_slides())
