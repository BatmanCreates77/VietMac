"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  RefreshCw,
  Smartphone,
  Globe,
  Calculator,
  TrendingDown,
  Shield,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import MacBookPricesTable from "@/components/ui/macbook-prices-table";

export default function MacBookTracker() {
  const [allPrices, setAllPrices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [exchangeRate, setExchangeRate] = useState(null);

  const fetchPrices = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/macbook-prices");
      const data = await response.json();

      if (data.success) {
        // Combine all marketplace data into a single array with shop name
        const combinedPrices = [
          ...data.marketplaces.fptShop.map((item) => ({
            ...item,
            shop: "FPT Shop",
          })),
          ...data.marketplaces.shopDunk.map((item) => ({
            ...item,
            shop: "ShopDunk",
          })),
          ...data.marketplaces.topZone.map((item) => ({
            ...item,
            shop: "TopZone",
          })),
          ...data.marketplaces.cellphones.map((item) => ({
            ...item,
            shop: "CellphoneS",
          })),
        ];

        setAllPrices(combinedPrices);
        setExchangeRate(data.exchangeRate);
        setLastUpdate(new Date().toLocaleString());
        toast.success("Prices updated successfully from all marketplaces!");
      } else {
        toast.error(data.error || "Failed to fetch prices");
      }
    } catch (error) {
      console.error("Error fetching prices:", error);
      toast.error("Failed to connect to price service");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrices();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4 md:p-8">
      <div className="container mx-auto max-w-7xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 rounded-full mb-6">
            <Sparkles className="h-4 w-4 text-indigo-600" />
            <span className="text-sm font-medium text-indigo-700">
              Best MacBook Deals in Vietnam
            </span>
          </div>

          <div className="flex justify-center items-center gap-3 mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-indigo-600 blur-xl opacity-20"></div>
              <Smartphone className="h-12 w-12 text-indigo-600 relative" />
            </div>
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gray-900 via-indigo-900 to-blue-900 bg-clip-text text-transparent">
              VietMac Compare
            </h1>
          </div>

          <p className="text-xl text-gray-600 mb-6 max-w-2xl mx-auto">
            Live MacBook Pro 16" prices from Vietnam's top Apple retailers with
            <span className="font-semibold text-green-600">
              {" "}
              VAT refunds
            </span>{" "}
            for Indian tourists
          </p>

          <div className="flex justify-center items-center gap-6 text-sm text-gray-600 flex-wrap">
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm">
              <Globe className="h-5 w-5 text-blue-500" />
              <span className="font-medium">4 Top Retailers</span>
            </div>
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm">
              <TrendingDown className="h-5 w-5 text-green-500" />
              <span className="font-medium">8.5% VAT Refund</span>
            </div>
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm">
              <Shield className="h-5 w-5 text-indigo-500" />
              <span className="font-medium">Live Pricing</span>
            </div>
          </div>
        </div>

        {exchangeRate && (
          <Card className="mb-8 bg-white/95 backdrop-blur-md shadow-lg border-0 ring-1 ring-gray-200/50">
            <CardContent className="pt-6">
              <div className="flex justify-between items-center flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg">
                    <Calculator className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 font-medium">
                      Exchange Rate
                    </div>
                    <div className="text-lg font-bold text-gray-900">
                      1 INR ={" "}
                      <span className="text-indigo-600">
                        {exchangeRate.toFixed(4)}
                      </span>{" "}
                      VND
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {lastUpdate && (
                    <span className="text-xs text-gray-500 font-medium">
                      Updated: {lastUpdate}
                    </span>
                  )}
                  <Button
                    onClick={fetchPrices}
                    disabled={loading}
                    size="lg"
                    className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all"
                  >
                    <RefreshCw
                      className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
                    />
                    Refresh Prices
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {loading && allPrices.length === 0 ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 animate-spin text-indigo-600 mx-auto mb-4" />
              <p className="text-gray-600">
                Fetching live prices from Vietnam...
              </p>
            </div>
          </div>
        ) : (
          <MacBookPricesTable data={allPrices} />
        )}

        <Card className="mt-8 bg-white/95 backdrop-blur-md shadow-lg border-0 ring-1 ring-gray-200/50">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-gray-900">
              Tracked MacBook Pro Models
            </CardTitle>
            <CardDescription className="text-base text-gray-600">
              Base and Top configurations for each chip variant
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="border-2 border-indigo-100 rounded-xl p-5 bg-gradient-to-br from-indigo-50/50 to-white hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-2 w-2 rounded-full bg-indigo-500"></div>
                  <h3 className="font-bold text-lg text-indigo-900">
                    M4 Pro Chip
                  </h3>
                </div>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-500 mt-0.5">▸</span>
                    <span>Base: 14-core CPU, 20-core GPU, 24GB, 512GB</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-500 mt-0.5">▸</span>
                    <span>Top: 14-core CPU, 20-core GPU, 48GB, 1TB</span>
                  </li>
                </ul>
              </div>
              <div className="border-2 border-purple-100 rounded-xl p-5 bg-gradient-to-br from-purple-50/50 to-white hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-2 w-2 rounded-full bg-purple-500"></div>
                  <h3 className="font-bold text-lg text-purple-900">
                    M4 Max Chip
                  </h3>
                </div>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-purple-500 mt-0.5">▸</span>
                    <span>Base: 14-core CPU, 32-core GPU, 36GB, 1TB</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-500 mt-0.5">▸</span>
                    <span>Top: 16-core CPU, 40-core GPU, 128GB, 2TB</span>
                  </li>
                </ul>
              </div>
              <div className="border-2 border-blue-100 rounded-xl p-5 bg-gradient-to-br from-blue-50/50 to-white hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                  <h3 className="font-bold text-lg text-blue-900">
                    M3 Max Chip
                  </h3>
                </div>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-500 mt-0.5">▸</span>
                    <span>Base: 14-core CPU, 30-core GPU, 36GB, 1TB</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-500 mt-0.5">▸</span>
                    <span>Top: 16-core CPU, 40-core GPU, 128GB, 2TB</span>
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <Card className="bg-white/95 backdrop-blur-md shadow-lg border-0 ring-1 ring-gray-200/50 hover:shadow-xl transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
                  <TrendingDown className="h-6 w-6 text-green-600" />
                </div>
                <CardTitle className="text-lg font-bold text-gray-900">
                  VAT Refund Info
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-gray-700 leading-relaxed">
              <p>
                Vietnam VAT on electronics is 10%, but effective tourist refund
                is <span className="font-semibold text-green-600">~8.5%</span>{" "}
                after airport processing fees. Minimum purchase: 2M VND.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/95 backdrop-blur-md shadow-lg border-0 ring-1 ring-gray-200/50 hover:shadow-xl transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                  <Globe className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle className="text-lg font-bold text-gray-900">
                  Why Buy in Vietnam?
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-gray-700 leading-relaxed">
              <p>
                Vietnam offers{" "}
                <span className="font-semibold text-blue-600">
                  competitive pricing
                </span>{" "}
                compared to India. All products come with official Apple
                warranty valid worldwide.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/95 backdrop-blur-md shadow-lg border-0 ring-1 ring-gray-200/50 hover:shadow-xl transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
                  <Shield className="h-6 w-6 text-purple-600" />
                </div>
                <CardTitle className="text-lg font-bold text-gray-900">
                  Live Updates
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-gray-700 leading-relaxed">
              <p>
                Prices and exchange rates are updated in{" "}
                <span className="font-semibold text-purple-600">real-time</span>{" "}
                from Vietnamese retailers. Click refresh for the latest data.
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="text-center mt-8 text-sm text-gray-500">
          <p>
            Prices scraped from official Vietnamese retailers (October 2025).
            Always verify final prices at the store. Bring your passport for VAT
            refund.
          </p>
        </div>
      </div>
    </div>
  );
}
