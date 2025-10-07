"use client";

import { Instrument_Serif } from "next/font/google";
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

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
});

export default function MacBookTracker() {
  const [allPrices, setAllPrices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exchangeRate, setExchangeRate] = useState(null);
  const [currency, setCurrency] = useState("INR");

  const fetchPrices = async (selectedCurrency) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/macbook-prices?currency=${selectedCurrency}`,
      );
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
        setCurrency(data.currency);
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
    fetchPrices(currency);
  }, [currency]);

  return (
    <div className="min-h-screen bg-black">
      {/* Header Section */}
      <div className="bg-black text-white py-6 px-4">
        <div className="container mx-auto max-w-7xl flex flex-col items-center">
          {/* Currency Selector - Top Right */}
          <div className="w-full flex justify-end mb-4">
            <Select value={currency} onValueChange={setCurrency}>
              <SelectTrigger className="w-[200px] bg-gray-900 border-gray-800 text-white">
                <SelectValue placeholder="Select currency" />
              </SelectTrigger>
              <SelectContent className="bg-gray-900 border-gray-800 text-white">
                <SelectItem value="INR">🇮🇳 Home Currency: INR</SelectItem>
                <SelectItem value="USD">🇺🇸 Home Currency: USD</SelectItem>
                <SelectItem value="EUR">🇪🇺 Home Currency: EUR</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Title with Sparkles */}
          <div className="relative mb-4 text-center">
            <h1
              className={`text-[42px] text-white not-italic whitespace-pre leading-normal relative z-10 ${instrumentSerif.className}`}
            >
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
            <div className="bg-gray-900 rounded-lg p-4 max-w-2xl w-full">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-lg font-bold mb-1">
                    Exchange Rate: 1 {currency} = {exchangeRate.toFixed(2)} VND
                  </div>
                  <div className="text-xs text-gray-400">Powered by Wise</div>
                </div>
                <Button
                  onClick={() => fetchPrices(currency)}
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
            <MacBookPricesTable data={allPrices} currency={currency} />
          )}

          {/* Disclaimer */}
          <div className="mt-8 text-sm text-gray-600 text-left bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="font-semibold text-gray-900 mb-2">
              💡 Important Notes:
            </p>
            <ul className="space-y-2 list-disc list-inside">
              <li>
                <strong>Online vs Physical Store:</strong> Prices shown are from
                online stores. Physical stores often allow bargaining -
                typically 2-5% discount for average negotiation, or 5-10% for
                skilled bargaining. Use the slider above to estimate savings.
              </li>
              <li>
                <strong>VAT Refund:</strong> To qualify for 8.5% VAT refund,
                purchase from authorized retail locations and ask for VAT refund
                documents. Refunds are processed at the airport (minus ~22%
                processing fee).
              </li>
              <li>
                <strong>Price Accuracy:</strong> Prices are indicative and
                subject to change. Always verify current prices at the store
                before purchasing.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
