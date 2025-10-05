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
import { RefreshCw, Smartphone, Globe, Calculator } from "lucide-react";
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="container mx-auto max-w-7xl">
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-2 mb-4">
            <Smartphone className="h-8 w-8 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-900">
              VietMac Compare
            </h1>
          </div>
          <p className="text-lg text-gray-600 mb-4">
            Live MacBook Pro 16" prices from Vietnam's top Apple retailers for
            Indian tourists
          </p>
          <div className="flex justify-center items-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Globe className="h-4 w-4" />
              <span>4 Major Vietnamese Retailers</span>
            </div>
            <div className="flex items-center gap-1">
              <Calculator className="h-4 w-4" />
              <span>8.5% VAT Refund Included</span>
            </div>
          </div>
        </div>

        {exchangeRate && (
          <Card className="mb-6 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="flex justify-between items-center flex-wrap gap-4">
                <div className="text-sm text-gray-600">
                  Current Exchange Rate:{" "}
                  <span className="font-semibold">
                    1 INR = {exchangeRate.toFixed(4)} VND
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  {lastUpdate && (
                    <span className="text-xs text-gray-500">
                      Last updated: {lastUpdate}
                    </span>
                  )}
                  <Button
                    onClick={fetchPrices}
                    disabled={loading}
                    size="sm"
                    className="bg-indigo-600 hover:bg-indigo-700"
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

        <Card className="mt-8 bg-white/90 backdrop-blur-sm shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-900">
              Tracked MacBook Pro Models
            </CardTitle>
            <CardDescription className="text-gray-600">
              Base and Top configurations for each chip variant
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M4 Pro Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 14-core CPU, 20-core GPU, 24GB, 512GB</li>
                  <li>• Top: 14-core CPU, 20-core GPU, 48GB, 1TB</li>
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M4 Max Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 14-core CPU, 32-core GPU, 36GB, 1TB</li>
                  <li>• Top: 16-core CPU, 40-core GPU, 128GB, 2TB</li>
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M3 Max Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 14-core CPU, 30-core GPU, 36GB, 1TB</li>
                  <li>• Top: 16-core CPU, 40-core GPU, 128GB, 2TB</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Calculator className="h-5 w-5 text-indigo-600" />
                VAT Refund Info
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              <p>
                Vietnam VAT on electronics is 10%, but effective tourist refund
                is ~8.5% after airport processing fees. Minimum purchase: 2M
                VND.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Globe className="h-5 w-5 text-green-600" />
                Why Buy in Vietnam?
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              <p>
                Vietnam offers competitive MacBook pricing compared to India.
                All products come with official Apple warranty valid worldwide.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Smartphone className="h-5 w-5 text-blue-600" />
                Live Updates
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              <p>
                Prices and exchange rates are updated in real-time from
                Vietnamese retailers. Click refresh for the latest data.
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
