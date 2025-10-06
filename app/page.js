"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";
import MacBookPricesTable from "@/components/ui/macbook-prices-table";
import { SparklesCore } from "@/components/ui/sparkles";

export default function MacBookTracker() {
  const [allPrices, setAllPrices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exchangeRate, setExchangeRate] = useState(null);
  const [currency, setCurrency] = useState("INR");

  const fetchPrices = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/macbook-prices");
      const data = await response.json();
      if (data.success) {
        const combinedPrices = [
          ...data.marketplaces.fptShop.map((item) => ({
            ...item,
            shop: "FPTShop",
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
            shop: "CelphoneS",
          })),
        ];
        setAllPrices(combinedPrices);
        setExchangeRate(data.exchangeRate);
        toast.success("Prices updated successfully!");
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
    <div className="min-h-screen bg-black">
      {/* Header Section */}
      <div className="bg-black text-white py-6 px-4">
        <div className="container mx-auto max-w-7xl">
          {/* Currency Selector - Top Right */}
          <div className="flex justify-end mb-4">
            <Select value={currency} onValueChange={setCurrency}>
              <SelectTrigger className="w-[200px] bg-gray-900 border-gray-800 text-white">
                <SelectValue placeholder="Select currency" />
              </SelectTrigger>
              <SelectContent className="bg-gray-900 border-gray-800">
                <SelectItem value="INR">🇮🇳 Home Currency: INR</SelectItem>
                <SelectItem value="USD">🇺🇸 Home Currency: USD</SelectItem>
                <SelectItem value="EUR">🇪🇺 Home Currency: EUR</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Title with Sparkles */}
          <div className="relative mb-4">
            <h1 className="text-3xl md:text-4xl text-center font-serif relative z-10">
              Why pay more for a mac
            </h1>
            <div className="absolute inset-0 h-full w-full">
              <SparklesCore
                id="tsparticlesfullpage"
                background="transparent"
                minSize={0.6}
                maxSize={1.4}
                particleDensity={100}
                className="w-full h-full"
                particleColor="#FFFFFF"
              />
            </div>
          </div>

          {/* Subtitle */}
          <p className="text-center text-gray-400 text-base mb-4">
            Live MacBook prices from Vietnam's top Apple retailers with VAT
            refunds for tourists
          </p>

          {/* Exchange Rate Card */}
          {exchangeRate && (
            <div className="bg-gray-900 rounded-lg p-4 max-w-2xl mx-auto">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-xl font-bold mb-1">
                    Exchange Rate: 1 INR = {exchangeRate.toFixed(2)} VND
                  </div>
                  <div className="text-xs text-gray-400">Powered by Wise</div>
                </div>
                <Button
                  onClick={fetchPrices}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
                  />
                  Refresh Prices
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filters and Table Section */}
      <div className="bg-gray-50 py-8 px-4">
        <div className="container mx-auto max-w-7xl">
          {loading && allPrices.length === 0 ? (
            <div className="flex justify-center items-center py-12">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
                <p className="text-gray-600">
                  Fetching live prices from Vietnam...
                </p>
              </div>
            </div>
          ) : (
            <MacBookPricesTable data={allPrices} />
          )}

          {/* Disclaimer */}
          <div className="mt-8 text-sm text-gray-600 text-center">
            <p>
              Disclaimer: The prices listed are indicative and subject to
              change. To qualify for a VAT refund, you must purchase the device
              from authorized retail locations. Please note that these prices
              are sourced from online store.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
