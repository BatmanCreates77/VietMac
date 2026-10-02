import { NextResponse } from "next/server";
import { vatPercentOn, vatRefundFor } from "@/lib/vat-refund";

import { readFileSync } from "fs";
import { join } from "path";

// Load the scraper's output: { products, timestamp }
function loadScrapedData() {
  try {
    const filePath = join(
      process.cwd(),
      "macbook_scraper",
      "output",
      "latest_products.json",
    );
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    return { products: data.products || [], timestamp: data.timestamp || null };
  } catch (error) {
    console.error("Error loading scraped data:", error.message);
    return { products: [], timestamp: null };
  }
}

// Transform scraped product to marketplace product format
function transformScrapedProduct(product) {
  const modelName = product.model || "";
  const modelLower = modelName.toLowerCase();
  const specs = product.specs || {};
  // Data written before iPhones were added has no product_line: all Macs.
  const productLine = product.product_line || "mac";
  const common = {
    productLine,
    configuration: modelName, // Use full original name as configuration
    id: modelName.toLowerCase().replace(/\s+/g, "-").substring(0, 100),
    vndPrice: product.price_vnd,
    url: product.url,
    available: true,
    shop: product.shop,
    storage: specs.storage_display || "",
    storageGb: specs.storage_gb || null,
    scrapedAt: product.scraped_at || null,
    // True when this shop's latest scrape failed and these are its
    // last-known-good prices carried forward by the scraper.
    stale: Boolean(product.stale),
  };

  if (productLine === "iphone") {
    const modelType = specs.model_type || "iPhone";
    return {
      ...common,
      model: modelType,
      modelType,
      screenSize: "",
      category: "",
    };
  }

  // Prefer the scraper's parsed specs; the name-based guesses below are only
  // a fallback (a bare "pro" check misfiles "MacBook Neo ... A18 Pro").
  let modelType = specs.model_type || "MacBook";
  if (!specs.model_type) {
    if (modelLower.includes("air")) modelType = "MacBook Air";
    else if (modelLower.includes("pro")) modelType = "MacBook Pro";
  }

  let screenSize = specs.screen_size || "";
  if (!screenSize) {
    if (modelType === "MacBook Air") {
      if (modelLower.includes("13")) screenSize = '13"';
      else if (modelLower.includes("15")) screenSize = '15"';
    } else if (modelType === "MacBook Pro") {
      if (modelLower.includes("14")) screenSize = '14"';
      else if (modelLower.includes("16")) screenSize = '16"';
    }
  }

  let category = "Unknown";
  if (specs.chip) {
    category = specs.chip_variant ? `${specs.chip} ${specs.chip_variant}` : specs.chip;
  } else {
    if (modelLower.includes("m5 max")) category = "M5 Max";
    else if (modelLower.includes("m5 pro")) category = "M5 Pro";
    else if (modelLower.includes("m5")) category = "M5";
    else if (modelLower.includes("m4 max")) category = "M4 Max";
    else if (modelLower.includes("m4 pro")) category = "M4 Pro";
    else if (modelLower.includes("m4")) category = "M4";
    else if (modelLower.includes("m3 max")) category = "M3 Max";
    else if (modelLower.includes("m3 pro")) category = "M3 Pro";
    else if (modelLower.includes("m3")) category = "M3";
    else if (modelLower.includes("m2")) category = "M2";
    else if (modelLower.includes("m1")) category = "M1";
    else if (modelLower.includes("a18 pro")) category = "A18 Pro"; // MacBook Neo
    else if (modelType === "MacBook Neo") category = "A18 Pro";
  }

  return {
    ...common,
    model: screenSize ? `${modelType} ${screenSize}` : modelType,
    modelType: modelType,
    screenSize: screenSize,
    category: category,
  };
}

// Filter out used/refurbished products and invalid prices
function filterValidProducts(products) {
  return products.filter((p) => {
    // Filter out used MacBooks (keywords: Cũ, Trôi BH, Like New, Refurbished)
    const modelLower = (p.model || "").toLowerCase();
    const rawNameLower = (p.raw_name || "").toLowerCase();
    const isUsed =
      modelLower.includes("cũ") ||
      modelLower.includes("trôi bh") ||
      modelLower.includes("like new") ||
      modelLower.includes("refurbished") ||
      rawNameLower.includes("cũ") ||
      rawNameLower.includes("trôi bh");

    // Filter out invalid prices (less than 1 million VND)
    const hasValidPrice = p.price_vnd && p.price_vnd >= 1000000;

    return !isUsed && hasValidPrice;
  });
}

// Marketplace prices, from scraped data only. A shop with no scraped data
// (TopZone today — its site is unreachable from the scraper's network)
// returns an empty list: invented "estimate" prices used to be shown in
// their place, unlabeled, as if they were that shop's real prices.
function getMarketplacePrices(scrapedProducts) {
  const valid = filterValidProducts(scrapedProducts);
  const forShop = (shop) =>
    valid.filter((p) => p.shop === shop).map(transformScrapedProduct);

  return {
    fptShop: forShop("fptshop"),
    shopDunk: forShop("shopdunk"),
    topZone: forShop("topzone"),
    cellphones: forShop("cellphones"),
  };
}

async function getExchangeRateFromWise(currency = "INR") {
  const currencySymbols = {
    INR: "₹",
    USD: "$",
    EUR: "€",
  };
  const symbol =
    currencySymbols[currency.toUpperCase()] || currency.toUpperCase();
  const url = `https://wise.com/in/currency-converter/${currency.toLowerCase()}-to-vnd-rate`;

  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
    });

    if (response.ok) {
      const html = await response.text();
      const regex = new RegExp(
        `${symbol}1\s*${currency.toUpperCase()}\s*=\s*([\d.,]+)\s*VND`,
        "i",
      );
      const rateMatch = html.match(regex);
      if (rateMatch && rateMatch[1]) {
        const rate = parseFloat(rateMatch[1].replace(/,/g, ""));
        if (rate > 0) {
          console.log("✅ Wise rate:", rate);
          return rate;
        }
      }
    }
  } catch (error) {
    console.log(`❌ Wise error for ${currency}:`, error.message);
  }
  return null;
}

async function getExchangeRate(currency = "INR") {
  try {
    const wiseRate = await getExchangeRateFromWise(currency);
    if (wiseRate) return wiseRate;

    const response = await fetch(
      `https://api.exchangerate-api.com/v4/latest/${currency.toUpperCase()}`,
    );
    const data = await response.json();
    if (data.rates.VND) {
      console.log("✅ ExchangeRate-API:", data.rates.VND);
      return data.rates.VND;
    }
  } catch (error) {
    console.error("Exchange rate error:", error);
  }
  // Fallback rates
  const fallbackRates = {
    INR: 298,
    USD: 25000,
    EUR: 27000,
  };
  return fallbackRates[currency.toUpperCase()] || fallbackRates.INR;
}

function calculatePrices(priceData, exchangeRate) {
  return priceData.map((item) => {
    if (!item.vndPrice) {
      return {
        ...item,
        convertedPrice: null,
        vatRefund: null,
        finalPrice: null,
      };
    }

    const convertedPrice = item.vndPrice / exchangeRate;
    const vatRefund = vatRefundFor(convertedPrice);
    const finalPrice = convertedPrice - vatRefund;

    return {
      ...item,
      convertedPrice: Math.round(convertedPrice),
      vatRefund: Math.round(vatRefund),
      finalPrice: Math.round(finalPrice),
    };
  });
}

export async function GET(request) {
  try {
    const { pathname, searchParams } = new URL(request.url);
    const currency = searchParams.get("currency") || "INR";

    if (pathname.includes("/api/macbook-prices")) {
      console.log(`🔄 Fetching prices for ${currency}...`);
      const exchangeRate = await getExchangeRate(currency);

      const scraped = loadScrapedData();
      const marketplacePrices = getMarketplacePrices(scraped.products);

      const fptWithConverted = calculatePrices(
        marketplacePrices.fptShop,
        exchangeRate,
      );
      const shopDunkWithConverted = calculatePrices(
        marketplacePrices.shopDunk,
        exchangeRate,
      );
      const topZoneWithConverted = calculatePrices(
        marketplacePrices.topZone,
        exchangeRate,
      );
      const cellphonesWithConverted = calculatePrices(
        marketplacePrices.cellphones,
        exchangeRate,
      );

      const scrapedCount = Object.values(marketplacePrices).reduce(
        (sum, products) => sum + products.length,
        0,
      );

      return NextResponse.json({
        success: true,
        marketplaces: {
          fptShop: fptWithConverted,
          shopDunk: shopDunkWithConverted,
          topZone: topZoneWithConverted,
          cellphones: cellphonesWithConverted,
        },
        exchangeRate: exchangeRate,
        currency: currency.toUpperCase(),
        vatPercent: vatPercentOn(),
        timestamp: new Date().toISOString(),
        source: "Scraped from retailer websites",
        scrapedProductsCount: scrapedCount,
        // When the scraper last ran (its local time, as the scraper wrote
        // it) — not the time of this request.
        lastScraped: scraped.timestamp,
      });
    }

    if (pathname.includes("/api/health")) {
      return NextResponse.json({
        status: "healthy",
        timestamp: new Date().toISOString(),
      });
    }

    return NextResponse.json({ error: "Endpoint not found" }, { status: 404 });
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 },
    );
  }
}

export async function POST(request) {
  return NextResponse.json({ error: "Method not allowed" }, { status: 405 });
}
