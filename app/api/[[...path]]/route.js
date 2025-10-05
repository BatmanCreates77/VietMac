import { NextResponse } from 'next/server'
import puppeteer from 'puppeteer'

const MACBOOK_MODELS = [
  {
    model: 'MacBook Pro 16"',
    configuration: 'M3 Max, 36GB RAM, 1TB SSD',
    id: 'm3-max-36-1tb'
  },
  {
    model: 'MacBook Pro 16"',
    configuration: 'M4 Pro, 24GB RAM, 512GB SSD',
    id: 'm4-pro-24-512gb'
  },
  {
    model: 'MacBook Pro 16"',
    configuration: 'M4 Max, 36GB RAM, 1TB SSD',
    id: 'm4-max-36-1tb'
  },
  {
    model: 'MacBook Pro 16"',
    configuration: 'M4 Max, 48GB RAM, 1TB SSD',
    id: 'm4-max-48-1tb'
  }
]

async function getExchangeRateFromWise() {
  try {
    const response = await fetch('https://wise.com/in/currency-converter/inr-to-vnd-rate', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
      }
    })
    
    if (response.ok) {
      const html = await response.text()
      console.log('📡 Fetched Wise page, parsing for rate...')
      
      // Simple string search for the rate pattern we saw: ₹1 INR = 297.2 VND
      const rateMatch = html.match(/₹1\s*INR\s*=\s*([\d.,]+)\s*VND/i)
      if (rateMatch && rateMatch[1]) {
        const rate = parseFloat(rateMatch[1].replace(/,/g, ''))
        if (rate > 250 && rate < 350) {
          console.log('✅ Successfully extracted rate from Wise:', rate)
          return rate
        }
      }
      
      // Fallback: look for JSON data with rate
      const jsonMatch = html.match(/"rate"\s*:\s*([\d.]+)/)
      if (jsonMatch && jsonMatch[1]) {
        const rate = parseFloat(jsonMatch[1])
        if (rate > 250 && rate < 350) {
          console.log('✅ Successfully extracted rate from Wise JSON:', rate)
          return rate
        }
      }
      
      console.log('⚠️ Could not find rate in Wise HTML')
    } else {
      console.log('❌ Wise page request failed:', response.status)
    }
  } catch (error) {
    console.log('❌ Error fetching from Wise page:', error.message)
  }
  
  return null
}

async function getExchangeRate() {
  try {
    // Method 1: Try Wise's currency converter page
    const wiseRate = await getExchangeRateFromWise()
    if (wiseRate) {
      return wiseRate
    }
    
    // Method 2: Fallback to exchangerate-api.com (reliable free tier)
    const response = await fetch('https://api.exchangerate-api.com/v4/latest/INR')
    const data = await response.json()
    const rate = data.rates.VND
    
    if (rate) {
      console.log('✅ Fetched rate from ExchangeRate-API (fallback):', rate)
      return rate
    }
    
    throw new Error('No rate available from any source')
    
  } catch (error) {
    console.error('Exchange rate fetch error:', error)
    // Realistic fallback rate based on current market
    console.log('📍 Using fallback rate: 298')
    return 298
  }
}

function getMockPriceData() {
  // Realistic pricing based on Apple's official 2025 pricing converted to VND
  // Base M4 Pro starts at $2,499 USD ≈ 63M VND
  return [
    {
      model: 'MacBook Pro 16"',
      configuration: 'M3 Max, 36GB RAM, 1TB SSD',
      vndPrice: 89990000, // ~$3,600 USD (Previous gen, premium config)
      available: true,
      id: 'm3-max-36-1tb'
    },
    {
      model: 'MacBook Pro 16"',
      configuration: 'M4 Pro, 24GB RAM, 512GB SSD',
      vndPrice: 74990000, // ~$2,999 USD (Current gen, mid-tier)
      available: true,
      id: 'm4-pro-24-512gb'
    },
    {
      model: 'MacBook Pro 16"',
      configuration: 'M4 Max, 36GB RAM, 1TB SSD',
      vndPrice: 99990000, // ~$4,000 USD (Current gen, high-end)
      available: true,
      id: 'm4-max-36-1tb'
    },
    {
      model: 'MacBook Pro 16"',
      configuration: 'M4 Max, 48GB RAM, 1TB SSD',
      vndPrice: 124990000, // ~$5,000 USD (Top-tier config)
      available: true, // Changed to available
      id: 'm4-max-48-1tb'
    }
  ]
}

function calculatePrices(priceData, exchangeRate) {
  return priceData.map(item => {
    if (!item.vndPrice) {
      return {
        ...item,
        inrPrice: null,
        vatRefund: null,
        finalPrice: null
      }
    }
    
    const inrPrice = item.vndPrice / exchangeRate
    const vatRefund = inrPrice * 0.085
    const finalPrice = inrPrice - vatRefund
    
    return {
      ...item,
      inrPrice: Math.round(inrPrice),
      vatRefund: Math.round(vatRefund),
      finalPrice: Math.round(finalPrice)
    }
  })
}

export async function GET(request) {
  try {
    const { pathname } = new URL(request.url)
    
    if (pathname.includes('/api/macbook-prices')) {
      console.log('Fetching MacBook prices...')
      
      const exchangeRate = await getExchangeRate()
      console.log('Exchange rate (INR to VND):', exchangeRate)
      
      // Using mock data for now - will implement scraper next
      const priceData = getMockPriceData()
      
      const finalPrices = calculatePrices(priceData, exchangeRate)
      
      return NextResponse.json({
        success: true,
        prices: finalPrices,
        exchangeRate: exchangeRate,
        timestamp: new Date().toISOString(),
        source: 'Estimated Pricing (Based on Apple Official Rates + Vietnam Market)'
      })
    }
    
    if (pathname.includes('/api/health')) {
      return NextResponse.json({
        status: 'healthy',
        timestamp: new Date().toISOString()
      })
    }
    
    return NextResponse.json({ error: 'Endpoint not found' }, { status: 404 })
    
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: error.message,
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    )
  }
}

export async function POST(request) {
  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 })
}