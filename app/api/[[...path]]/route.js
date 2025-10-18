import { NextResponse } from "next/server";

import { readFileSync } from "fs";
import { join } from "path";

// Load scraped data from the scraper output
function loadScrapedData() {
  try {
    const filePath = join(
      process.cwd(),
      "macbook_scraper",
      "output",
      "latest_products.json",
    );
    const jsonData = readFileSync(filePath, "utf-8");
    const data = JSON.parse(jsonData);
    return data.products || [];
  } catch (error) {
    console.error("Error loading scraped data:", error.message);
    return [];
  }
}

// Transform scraped product to marketplace product format
function transformScrapedProduct(product) {
  // Parse basic info from model name
  const modelName = product.model || "";
  const modelLower = modelName.toLowerCase();

  // Extract model type
  let modelType = "MacBook";
  let screenSize = "";
  if (modelLower.includes("air")) {
    modelType = "MacBook Air";
    if (modelLower.includes("13")) screenSize = '13"';
    else if (modelLower.includes("15")) screenSize = '15"';
  } else if (modelLower.includes("pro")) {
    modelType = "MacBook Pro";
    if (modelLower.includes("14")) screenSize = '14"';
    else if (modelLower.includes("16")) screenSize = '16"';
  }

  // Extract chip/category - prefer specs.chip if available
  let category = "Unknown";

  // First try to use the parsed chip from specs
  if (product.specs && product.specs.chip) {
    const chip = product.specs.chip;
    const variant = product.specs.chip_variant;
    if (variant) {
      category = `${chip} ${variant}`; // e.g., "M5 Pro", "M4 Max"
    } else {
      category = chip; // e.g., "M5", "M4"
    }
  } else {
    // Fallback to parsing from model name
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
  }

  return {
    model: screenSize ? `${modelType} ${screenSize}` : modelType,
    modelType: modelType,
    screenSize: screenSize,
    category: category,
    configuration: modelName, // Use full original name as configuration
    id: modelName.toLowerCase().replace(/\s+/g, "-").substring(0, 100),
    vndPrice: product.price_vnd,
    url: product.url,
    available: true,
    shop: product.shop, // Keep shop info
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

// Get all marketplace prices from scraped data + hardcoded fallbacks
function getMarketplacePrices() {
  const scrapedProducts = loadScrapedData();
  const validProducts = filterValidProducts(scrapedProducts);

  console.log("🔍 Debug - Scraped products:", scrapedProducts.length);
  console.log("🔍 Debug - Valid products:", validProducts.length);

  // Group scraped products by shop
  const cellphonesProducts = validProducts
    .filter((p) => p.shop === "cellphones")
    .map((p) => {
      // Debug ALL cellphones products
      console.log("📱 CellphoneS product:", {
        model: p.model?.substring(0, 50),
        hasSpecs: !!p.specs,
        chip: p.specs?.chip,
        shop: p.shop,
      });
      return transformScrapedProduct(p);
    });

  const shopDunkProducts = validProducts
    .filter((p) => p.shop === "shopdunk")
    .map(transformScrapedProduct);

  console.log("🔍 Debug - CellphoneS products:", cellphonesProducts.length);
  console.log("🔍 Debug - ShopDunk products:", shopDunkProducts.length);

  // Hardcoded fallback products for FPT Shop and TopZone (not scraped)
  const baseProducts = [
    // MacBook Air M1 - 13" (Budget option)
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M1",
      configuration: "M1, 8-core CPU, 7-core GPU, 8GB, 256GB",
      id: "m1-air-13-8-256",
      vndPrice: 16890000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m1-2020",
      available: true,
    },
    // MacBook Air M2 - 13"
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M2",
      configuration: "M2, 8-core CPU, 8-core GPU, 8GB, 256GB",
      id: "m2-air-13-8-256",
      vndPrice: 24990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m2-2022-13-inch",
      available: true,
    },
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M2",
      configuration: "M2, 8-core CPU, 8-core GPU, 16GB, 256GB",
      id: "m2-air-13-16-256",
      vndPrice: 24990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m2-2022-13-inch",
      available: true,
    },
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M2",
      configuration: "M2, 8-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m2-air-13-16-512",
      vndPrice: 28990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m2-13-inch-2022-8cpu-10gpu-16gb-512gb",
      available: true,
    },
    // MacBook Air M2 - 15"
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M2",
      configuration: "M2, 8-core CPU, 10-core GPU, 8GB, 256GB",
      id: "m2-air-15-8-256",
      vndPrice: 30990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m2-2023-15-inch",
      available: true,
    },
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M2",
      configuration: "M2, 8-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m2-air-15-16-512",
      vndPrice: 40990000,
      available: true,
    },
    // MacBook Air M3 - 13"
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M3",
      configuration: "M3, 8-core CPU, 8-core GPU, 8GB, 256GB",
      id: "m3-air-13-8-256",
      vndPrice: 26990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m3-13-2024-8cpu-8gpu-8gb-256gb",
      available: true,
    },
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M3",
      configuration: "M3, 8-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m3-air-13-16-512",
      vndPrice: 37990000,
      available: true,
    },
    // MacBook Air M3 - 15"
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M3",
      configuration: "M3, 8-core CPU, 10-core GPU, 8GB, 256GB",
      id: "m3-air-15-8-256",
      vndPrice: 34990000,
      available: true,
    },
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M3",
      configuration: "M3, 8-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m3-air-15-16-512",
      vndPrice: 43990000,
      available: true,
    },
    // MacBook Air M4 - 13" (New 2025)
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M4",
      configuration: "M4, 10-core CPU, 8-core GPU, 16GB, 256GB",
      id: "m4-air-13-16-256",
      vndPrice: 25090000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m4-13-2025",
      available: true,
    },
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m4-air-13-16-512",
      vndPrice: 30790000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m4-13-2025",
      available: true,
    },
    {
      model: 'MacBook Air 13"',
      modelType: "MacBook Air",
      screenSize: '13"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 24GB, 512GB",
      id: "m4-air-13-24-512",
      vndPrice: 36990000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m4-13-2025",
      available: true,
    },
    // MacBook Air M4 - 15" (New 2025)
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 16GB, 256GB",
      id: "m4-air-15-16-256",
      vndPrice: 29290000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m4-15-2025",
      available: true,
    },
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m4-air-15-16-512",
      vndPrice: 33990000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m4-15-2025",
      available: true,
    },
    {
      model: 'MacBook Air 15"',
      modelType: "MacBook Air",
      screenSize: '15"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 24GB, 512GB",
      id: "m4-air-15-24-512",
      vndPrice: 41990000,
      fptUrl: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-air-m4-15-2025",
      available: true,
    },
    // MacBook Pro M4 - 14"
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 16GB, 512GB",
      id: "m4-pro-14-16-512",
      vndPrice: 39990000,
      available: true,
    },
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M4",
      configuration: "M4, 10-core CPU, 10-core GPU, 24GB, 1TB",
      id: "m4-pro-14-24-1tb",
      vndPrice: 49990000,
      available: true,
    },
    // MacBook Pro M4 Pro - 14"
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M4 Pro",
      configuration: "M4 Pro, 12-core CPU, 16-core GPU, 24GB, 512GB",
      id: "m4pro-pro-14-24-512",
      vndPrice: 56990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-m4-pro-14-2024-12cpu-16gpu-24gb-512gb",
      available: true,
    },
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M4 Pro",
      configuration: "M4 Pro, 14-core CPU, 20-core GPU, 24GB, 1TB",
      id: "m4pro-pro-14-24-1tb",
      vndPrice: 64990000,
      available: true,
    },
    // MacBook Pro M4 Pro - 16"
    {
      model: 'MacBook Pro 16"',
      modelType: "MacBook Pro",
      screenSize: '16"',
      category: "M4 Pro",
      configuration: "M4 Pro, 14-core CPU, 20-core GPU, 24GB, 512GB",
      id: "m4pro-base-24-512gb",
      vndPrice: 64990000,
      available: true,
    },
    {
      model: 'MacBook Pro 16"',
      modelType: "MacBook Pro",
      screenSize: '16"',
      category: "M4 Pro",
      configuration: "M4 Pro, 14-core CPU, 20-core GPU, 48GB, 1TB",
      id: "m4pro-top-48-1tb",
      vndPrice: 79990000,
      available: true,
    },
    // MacBook Pro M4 Max - 14"
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M4 Max",
      configuration: "M4 Max, 14-core CPU, 32-core GPU, 36GB, 1TB",
      id: "m4max-pro-14-36-1tb",
      vndPrice: 79990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-m4-max-14-2024-14cpu-32gpu-36gb-1tb",
      available: true,
    },
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M4 Max",
      configuration: "M4 Max, 16-core CPU, 40-core GPU, 48GB, 1TB",
      id: "m4max-pro-14-48-1tb",
      vndPrice: 102490000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-m4-max-14-2024-16cpu-40gpu-48gb-1tb",
      available: true,
    },
    // MacBook Pro M4 Max - 16"
    {
      model: 'MacBook Pro 16"',
      modelType: "MacBook Pro",
      screenSize: '16"',
      category: "M4 Max",
      configuration: "M4 Max, 14-core CPU, 32-core GPU, 36GB, 1TB",
      id: "m4max-base-36-1tb",
      vndPrice: 89990000,
      available: true,
    },
    {
      model: 'MacBook Pro 16"',
      modelType: "MacBook Pro",
      screenSize: '16"',
      category: "M4 Max",
      configuration: "M4 Max, 16-core CPU, 40-core GPU, 128GB, 2TB",
      id: "m4max-top-128-2tb",
      vndPrice: 164990000,
      available: true,
    },
    // MacBook Pro M3 - 14"
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M3",
      configuration: "M3, 8-core CPU, 10-core GPU, 8GB, 512GB",
      id: "m3-pro-14-8-512",
      vndPrice: 39990000,
      available: true,
    },
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M3",
      configuration: "M3, 8-core CPU, 10-core GPU, 16GB, 1TB",
      id: "m3-pro-14-16-1tb",
      vndPrice: 49990000,
      fptUrl:
        "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-m3-14-2024-8cpu-10gpu-16gb-1tb",
      available: true,
    },
    // MacBook Pro M3 Max - 14"
    {
      model: 'MacBook Pro 14"',
      modelType: "MacBook Pro",
      screenSize: '14"',
      category: "M3 Max",
      configuration: "M3 Max, 14-core CPU, 30-core GPU, 36GB, 1TB",
      id: "m3max-pro-14-36-1tb",
      vndPrice: 74990000,
      available: true,
    },
    // MacBook Pro M3 Max - 16"
    {
      model: 'MacBook Pro 16"',
      modelType: "MacBook Pro",
      screenSize: '16"',
      category: "M3 Max",
      configuration: "M3 Max, 14-core CPU, 30-core GPU, 36GB, 1TB",
      id: "m3max-base-36-1tb",
      vndPrice: 79990000,
      available: true,
    },
    {
      model: 'MacBook Pro 16"',
      modelType: "MacBook Pro",
      screenSize: '16"',
      category: "M3 Max",
      configuration: "M3 Max, 16-core CPU, 40-core GPU, 128GB, 2TB",
      id: "m3max-top-128-2tb",
      vndPrice: 149990000,
      available: true,
    },
  ];

  // Generate product-specific URLs
  const generateUrl = (product, shop) => {
    const modelSlug = product.model.toLowerCase().replace(/["\s]+/g, "-");
    const chipSlug = product.category.toLowerCase().replace(/\s+/g, "-");

    switch (shop) {
      case "fptShop":
        return `https://fptshop.com.vn/may-tinh-xach-tay?product=${modelSlug}-${chipSlug}`;
      case "shopDunk":
        return `https://shopdunk.com/${modelSlug}-${chipSlug}`;
      case "topZone":
        return `https://www.topzone.vn/${modelSlug}-${chipSlug}`;
      case "cellphones":
        return `https://cellphones.com.vn/apple/${modelSlug}-${chipSlug}.html`;
      default:
        return "#";
    }
  };

  // Merge scraped data with baseProducts (prefer scraped prices)
  const mergeProducts = (scraped, base) => {
    // For shops with scraped data, ONLY show scraped products (live prices)
    if (scraped.length > 0) {
      return scraped;
    }
    // For shops without scraped data, show fallback estimates
    return base.map((bp) => ({ ...bp, scraped: false }));
  };

  const fptShop = baseProducts.map((p) => ({
    ...p,
    url: p.fptUrl || "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook",
  }));

  const shopDunk = mergeProducts(
    shopDunkProducts,
    baseProducts.map((p) => ({
      ...p,
      vndPrice: p.vndPrice + 1000000,
      url: "https://shopdunk.com/mac",
    })),
  );

  const topZone = baseProducts.map((p) => ({
    ...p,
    vndPrice: p.vndPrice - 500000,
    url: "https://www.topzone.vn/apple/macbook",
  }));

  const cellphones = mergeProducts(
    cellphonesProducts,
    baseProducts.map((p) => ({
      ...p,
      vndPrice: p.vndPrice - 1000000,
      url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
    })),
  );

  return {
    fptShop,
    shopDunk,
    topZone,
    cellphones,
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
    // Correct VAT calculation: extract 8.5% tax from the total price
    // If price includes VAT: tax = (price × 8.5) / 108.5
    const vatRefundGross = (convertedPrice * 8.5) / 108.5;
    // Airport processing fee is ~22% of the refund (based on real user data)
    const vatRefund = vatRefundGross * 0.78;
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

      const marketplacePrices = getMarketplacePrices();

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

      // Count scraped vs fallback products
      const scrapedCount = [
        ...marketplacePrices.cellphones.filter((p) => p.scraped),
        ...marketplacePrices.shopDunk.filter((p) => p.scraped),
      ].length;

      const scrapedData = loadScrapedData();
      const lastUpdate =
        scrapedData && scrapedData.length > 0 ? new Date().toISOString() : null;

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
        timestamp: new Date().toISOString(),
        source: `Market Estimates`,
        scrapedProductsCount: scrapedCount,
        lastScraped: lastUpdate,
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
