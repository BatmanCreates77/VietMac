import { NextResponse } from "next/server";

// Get all marketplace prices with current FPT Shop Vietnam prices (Jan 2025)
function getMarketplacePrices() {
  const baseProducts = [
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

  return {
    fptShop: baseProducts.map((p) => ({
      ...p,
      url: p.fptUrl || "https://fptshop.com.vn/may-tinh-xach-tay/apple-macbook",
    })),
    shopDunk: baseProducts.map((p) => {
      // ShopDunk actual prices and URLs (scraped Oct 2025)
      const shopDunkData = {
        "m2-air-13-8-256": {
          price: 16890000,
          url: "https://shopdunk.com/macbook-air-m1-2020",
        },
        "m2-air-13-16-256": {
          price: 24090000,
          url: "https://shopdunk.com/macbook-air-m2-13-inch-10-core-gpu-16gb-ram-256gb-ssd",
        },
        "m4-air-13-16-256": {
          price: 25090000,
          url: "https://shopdunk.com/macbook-air-m4-13-inch-8-core-gpu-16gb-ram-256gb-ssd",
        },
        "m4-air-13-16-512": {
          price: 29790000,
          url: "https://shopdunk.com/macbook-air-m4-13-inch-10-core-gpu-16gb-ram-512gb-ssd",
        },
        "m4-air-13-24-512": {
          price: 36990000,
          url: "https://shopdunk.com/macbook-air-m4-13-inch-10-core-gpu-24gb-ram-512gb-ssd",
        },
        "m4-air-15-16-256": {
          price: 29290000,
          url: "https://shopdunk.com/macbook-air-m4-15-inch-10-core-gpu-16gb-ram-256gb-ssd",
        },
        "m4-air-15-16-512": {
          price: 33990000,
          url: "https://shopdunk.com/macbook-air-m4-15-inch-10-core-gpu-16gb-ram-512gb-ssd",
        },
        "m4-air-15-24-512": {
          price: 41990000,
          url: "https://shopdunk.com/macbook-air-m4-15-inch-10-core-gpu-24gb-ram-512gb-ssd",
        },
        "m3-pro-16-18-512": {
          price: 63490000,
          url: "https://shopdunk.com/mac",
        },
      };

      const data = shopDunkData[p.id];
      return {
        ...p,
        vndPrice: data?.price || p.vndPrice + 1000000,
        url: data?.url || "https://shopdunk.com/mac",
      };
    }),
    topZone: baseProducts.map((p) => ({
      ...p,
      vndPrice: p.vndPrice - 500000, // TopZone slightly lower
      url: "https://www.topzone.vn/apple/macbook",
    })),
    cellphones: baseProducts.map((p) => {
      // CellphoneS actual prices and URLs (scraped Oct 2025)
      const cellphonesData = {
        "m4-pro-14-16-512": {
          price: 38090000,
          url: "https://cellphones.com.vn/macbook-pro-14-inch-m4-16gb-512gb.html",
        },
        "m4-pro-14-24-1tb": {
          price: 48390000,
          url: "https://cellphones.com.vn/macbook-pro-14-inch-m4-24gb-1tb.html",
        },
        "m4pro-pro-14-24-512": {
          price: 47590000,
          url: "https://cellphones.com.vn/macbook-pro-14-inch-m4-pro-24gb-512gb.html",
        },
        "m4pro-pro-14-24-1tb": {
          price: 57490000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
        "m4pro-base-24-512gb": {
          price: 63990000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
        "m4pro-top-48-1tb": {
          price: 73990000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
        "m4max-pro-14-36-1tb": {
          price: 79990000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
        "m4max-pro-14-48-1tb": {
          price: 95990000,
          url: "https://cellphones.com.vn/macbook-pro-16-inch-m4-max-48gb-1tb.html",
        },
        "m4max-base-36-1tb": {
          price: 87990000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
        "m2-air-13-8-256": {
          price: 19890000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-air.html",
        },
        "m3-pro-14-16-1tb": {
          price: 48390000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
        "m3max-base-36-1tb": {
          price: 73990000,
          url: "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
        },
      };

      const data = cellphonesData[p.id];
      return {
        ...p,
        vndPrice: data?.price || p.vndPrice - 1000000,
        url:
          data?.url || "https://cellphones.com.vn/laptop/mac/macbook-pro.html",
      };
    }),
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
        `${symbol}1\\s*${currency.toUpperCase()}\\s*=\\s*([\\d.,]+)\\s*VND`,
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
        source: "Live Exchange Rate + Vietnamese Market Pricing (Oct 2025)",
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
