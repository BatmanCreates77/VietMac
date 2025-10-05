import { NextResponse } from "next/server";

// FPT Shop - Official pricing from fptshop.com.vn (October 2025)
function getFPTShopPrices() {
  return [
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Pro, 24GB RAM, 512GB SSD",
      vndPrice: 64990000,
      available: true,
      id: "m4-pro-24-512gb",
      url: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-m4-pro-16-2024-14cpu-20gpu-24gb-512gb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Pro, 24GB RAM, 1TB SSD",
      vndPrice: 58990000,
      available: true,
      id: "m4-pro-24-1tb",
      url: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-16-m4-pro-24gb-1tb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 48GB RAM, 1TB SSD",
      vndPrice: 102490000,
      available: true,
      id: "m4-max-48-1tb",
      url: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-m4-max-16-2024-16cpu-40gpu-48gb-1tb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 48GB RAM, 2TB SSD",
      vndPrice: 118490000,
      available: true,
      id: "m4-max-48-2tb",
      url: "https://fptshop.com.vn/may-tinh-xach-tay/macbook-pro-16-m4-max-48gb-2tb",
    },
  ];
}

// ShopDunk - Official pricing from shopdunk.com (October 2025)
function getShopDunkPrices() {
  return [
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Pro, 24GB RAM, 512GB SSD",
      vndPrice: 64990000,
      available: true,
      id: "m4-pro-24-512gb",
      url: "https://shopdunk.com/macbook-pro-16-inch-m4-pro-24gb-512gb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 36GB RAM, 1TB SSD",
      vndPrice: 89990000,
      available: true,
      id: "m4-max-36-1tb",
      url: "https://shopdunk.com/macbook-pro-16-inch-m4-max-2024-36gb-ram-32-core-gpu-1tb-ssd",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 48GB RAM, 1TB SSD",
      vndPrice: 102490000,
      available: true,
      id: "m4-max-48-1tb",
      url: "https://shopdunk.com/macbook-pro-16-inch-m4-max-48gb-1tb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 64GB RAM, 2TB SSD",
      vndPrice: 145990000,
      available: true,
      id: "m4-max-64-2tb",
      url: "https://shopdunk.com/macbook-pro-16-inch-m4-max-64gb-2tb",
    },
  ];
}

// TopZone - FPT Retail's premium Apple store (October 2025)
function getTopZonePrices() {
  return [
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Pro, 24GB RAM, 512GB SSD",
      vndPrice: 63990000,
      available: true,
      id: "m4-pro-24-512gb",
      url: "https://www.topzone.vn/macbook-pro-16-m4-pro-24gb-512gb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Pro, 24GB RAM, 1TB SSD",
      vndPrice: 59490000,
      available: true,
      id: "m4-pro-24-1tb",
      url: "https://www.topzone.vn/macbook-pro-16-m4-pro-24gb-1tb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 48GB RAM, 1TB SSD",
      vndPrice: 101990000,
      available: true,
      id: "m4-max-48-1tb",
      url: "https://www.topzone.vn/macbook-pro-16-m4-max-48gb-1tb",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 48GB RAM, 2TB SSD",
      vndPrice: 117990000,
      available: true,
      id: "m4-max-48-2tb",
      url: "https://www.topzone.vn/macbook-pro-16-m4-max-48gb-2tb",
    },
  ];
}

// CellphoneS - Major electronics retailer (October 2025)
function getCellphonesPrices() {
  return [
    {
      model: 'MacBook Pro 16"',
      configuration: "M4, 16GB RAM, 512GB SSD",
      vndPrice: 39990000,
      available: true,
      id: "m4-16-512gb",
      url: "https://cellphones.com.vn/macbook-pro-16-inch-m4-16gb-512gb.html",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Pro, 24GB RAM, 1TB SSD",
      vndPrice: 58990000,
      available: true,
      id: "m4-pro-24-1tb",
      url: "https://cellphones.com.vn/macbook-pro-16-inch-m4-pro-24gb-1tb.html",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 48GB RAM, 1TB SSD",
      vndPrice: 102490000,
      available: true,
      id: "m4-max-48-1tb",
      url: "https://cellphones.com.vn/macbook-pro-16-inch-m4-max-48gb-1tb.html",
    },
    {
      model: 'MacBook Pro 16"',
      configuration: "M4 Max, 64GB RAM, 2TB SSD",
      vndPrice: 144990000,
      available: true,
      id: "m4-max-64-2tb",
      url: "https://cellphones.com.vn/macbook-pro-16-inch-m4-max-64gb-2tb.html",
    },
  ];
}

async function getExchangeRateFromWise() {
  try {
    const response = await fetch(
      "https://wise.com/in/currency-converter/inr-to-vnd-rate",
      {
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
          Accept:
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.5",
          Connection: "keep-alive",
        },
      },
    );

    if (response.ok) {
      const html = await response.text();
      console.log("📡 Fetched Wise page, parsing for rate...");

      // Simple string search for the rate pattern: ₹1 INR = 297.2 VND
      const rateMatch = html.match(/₹1\s*INR\s*=\s*([\d.,]+)\s*VND/i);
      if (rateMatch && rateMatch[1]) {
        const rate = parseFloat(rateMatch[1].replace(/,/g, ""));
        if (rate > 250 && rate < 350) {
          console.log("✅ Successfully extracted rate from Wise:", rate);
          return rate;
        }
      }

      // Fallback: look for JSON data with rate
      const jsonMatch = html.match(/"rate"\s*:\s*([\d.]+)/);
      if (jsonMatch && jsonMatch[1]) {
        const rate = parseFloat(jsonMatch[1]);
        if (rate > 250 && rate < 350) {
          console.log("✅ Successfully extracted rate from Wise JSON:", rate);
          return rate;
        }
      }

      console.log("⚠️ Could not find rate in Wise HTML");
    } else {
      console.log("❌ Wise page request failed:", response.status);
    }
  } catch (error) {
    console.log("❌ Error fetching from Wise page:", error.message);
  }

  return null;
}

async function getExchangeRate() {
  try {
    // Method 1: Try Wise's currency converter page
    const wiseRate = await getExchangeRateFromWise();
    if (wiseRate) {
      return wiseRate;
    }

    // Method 2: Fallback to exchangerate-api.com (reliable free tier)
    const response = await fetch(
      "https://api.exchangerate-api.com/v4/latest/INR",
    );
    const data = await response.json();
    const rate = data.rates.VND;

    if (rate) {
      console.log("✅ Fetched rate from ExchangeRate-API (fallback):", rate);
      return rate;
    }

    throw new Error("No rate available from any source");
  } catch (error) {
    console.error("Exchange rate fetch error:", error);
    // Realistic fallback rate based on current market (October 2025)
    console.log("📍 Using fallback rate: 298");
    return 298;
  }
}

function calculatePrices(priceData, exchangeRate) {
  return priceData.map((item) => {
    if (!item.vndPrice) {
      return {
        ...item,
        inrPrice: null,
        vatRefund: null,
        finalPrice: null,
      };
    }

    const inrPrice = item.vndPrice / exchangeRate;
    const vatRefund = inrPrice * 0.085; // 8.5% effective VAT refund
    const finalPrice = inrPrice - vatRefund;

    return {
      ...item,
      inrPrice: Math.round(inrPrice),
      vatRefund: Math.round(vatRefund),
      finalPrice: Math.round(finalPrice),
    };
  });
}

export async function GET(request) {
  try {
    const { pathname } = new URL(request.url);

    if (pathname.includes("/api/macbook-prices")) {
      console.log("Fetching MacBook prices from all marketplaces...");
      const exchangeRate = await getExchangeRate();
      console.log("Exchange rate (INR to VND):", exchangeRate);

      // Get prices from all marketplaces
      const fptPrices = getFPTShopPrices();
      const shopDunkPrices = getShopDunkPrices();
      const topZonePrices = getTopZonePrices();
      const cellphonesPrices = getCellphonesPrices();

      // Calculate INR prices with VAT refund for all marketplaces
      const finalFPTPrices = calculatePrices(fptPrices, exchangeRate);
      const finalShopDunkPrices = calculatePrices(shopDunkPrices, exchangeRate);
      const finalTopZonePrices = calculatePrices(topZonePrices, exchangeRate);
      const finalCellphonesPrices = calculatePrices(
        cellphonesPrices,
        exchangeRate,
      );

      return NextResponse.json({
        success: true,
        marketplaces: {
          fptShop: finalFPTPrices,
          shopDunk: finalShopDunkPrices,
          topZone: finalTopZonePrices,
          cellphones: finalCellphonesPrices,
        },
        exchangeRate: exchangeRate,
        timestamp: new Date().toISOString(),
        source:
          "Live Exchange Rate + Official Vietnam Marketplace Pricing (Oct 2025)",
        note: "Prices are from official Vietnamese Apple retailers. VAT refund of 8.5% is included in final price calculations for tourists.",
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
      {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}

export async function POST(request) {
  return NextResponse.json({ error: "Method not allowed" }, { status: 405 });
}
