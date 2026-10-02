"use client";

import { Instrument_Serif } from "next/font/google";
import { useState, useEffect } from "react";
import { usePostHog } from "posthog-js/react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Laptop, RefreshCw, Smartphone } from "lucide-react";
import { toast } from "sonner";
import MacBookPricesTable from "@/components/ui/macbook-prices-table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { refundShareOfPrice, vatPercentOn } from "@/lib/vat-refund";
import { SparklesCore } from "@/components/ui/sparkles";
import { Squares } from "@/components/ui/squares-background";

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
});

const PRODUCT_TABS = [
  { value: "mac", label: "Mac", icon: Laptop, headline: "a mac" },
  { value: "iphone", label: "iPhone", icon: Smartphone, headline: "an iPhone" },
];

export default function MacBookTracker() {
  const posthog = usePostHog();
  const [allPrices, setAllPrices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exchangeRate, setExchangeRate] = useState(null);
  const [currency, setCurrency] = useState("INR");
  const [productLine, setProductLine] = useState("mac");

  // The tab lives in the URL (?tab=iphone) so it can be shared/bookmarked.
  // Read on mount rather than via useSearchParams, which would need a
  // Suspense boundary on this statically rendered page.
  useEffect(() => {
    const tab = new URLSearchParams(window.location.search).get("tab");
    if (PRODUCT_TABS.some((t) => t.value === tab)) setProductLine(tab);
  }, []);

  const selectProductLine = (tab) => {
    posthog?.capture("product_tab_selected", { product_line: tab });
    setProductLine(tab);
    const url = new URL(window.location.href);
    if (tab === "mac") url.searchParams.delete("tab");
    else url.searchParams.set("tab", tab);
    window.history.replaceState(null, "", url);
  };

  const activeTab = PRODUCT_TABS.find((t) => t.value === productLine);
  const countFor = (tab) =>
    allPrices.filter((item) => (item.productLine || "mac") === tab).length;

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
      <div className="relative bg-black text-white py-6 px-4 pb-32 overflow-hidden">
        {/* Squares Background */}
        <div className="absolute inset-0 w-full h-full -z-0">
          <Squares
            direction="diagonal"
            speed={0.5}
            borderColor="#1a1a1a"
            squareSize={40}
            hoverFillColor="#1a1a1a"
          />
        </div>

        <div className="container mx-auto max-w-7xl flex flex-col items-center relative z-10">
          {/* Currency Selector - Centered */}
          <div className="w-full flex justify-center mb-4 animate-in fade-in slide-in-from-top duration-500">
            <Select
              value={currency}
              onValueChange={(newCurrency) => {
                posthog?.capture("currency_changed", {
                  from: currency,
                  to: newCurrency,
                });
                setCurrency(newCurrency);
              }}
            >
              <SelectTrigger className="w-full sm:w-[200px] bg-gray-900 border-gray-800 text-white hover:bg-gray-800 transition-all duration-200">
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
          <div className="relative mb-4 text-center animate-in fade-in zoom-in-95 duration-700 delay-100">
            <h1
              className={`text-3xl md:text-[42px] text-white not-italic whitespace-pre-wrap md:whitespace-pre leading-tight md:leading-normal relative z-10 ${instrumentSerif.className}`}
            >
              Why pay more for {activeTab.headline}
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
          <p className="text-center text-gray-400 text-sm md:text-base mb-4 px-4 animate-in fade-in slide-in-from-bottom duration-700 delay-200">
            Live Mac and iPhone prices from Vietnam's top Apple retailers
            with VAT refunds for tourists
          </p>

          {/* Exchange Rate Card */}
          {exchangeRate && (
            <div className="bg-gray-900 rounded-lg p-4 max-w-2xl w-full animate-in fade-in slide-in-from-bottom duration-700 delay-300 hover:scale-[1.02] transition-transform">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex-1">
                  <div className="text-base sm:text-lg font-bold mb-1">
                    Exchange Rate: 1 {currency} = {exchangeRate.toFixed(2)} VND
                  </div>
                  <div className="text-xs text-gray-400">Powered by Wise</div>
                </div>
                <Button
                  onClick={() => {
                    posthog?.capture("refresh_prices_clicked", { currency });
                    fetchPrices(currency);
                  }}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 w-full sm:w-auto hover:scale-105 transition-all duration-200 active:scale-95"
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
      <div className="bg-gray-50 py-8 px-4 -mt-24 relative">
        <div className="container mx-auto max-w-7xl bg-white rounded-t-3xl shadow-2xl p-6 relative z-20">
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
            <>
              <Tabs value={productLine} onValueChange={selectProductLine}>
                <TabsList
                  aria-label="Product"
                  className="mb-6 h-12 w-full gap-1 rounded-full bg-gray-100 p-1 sm:w-auto"
                >
                  {PRODUCT_TABS.map(({ value, label, icon: Icon }) => (
                    <TabsTrigger
                      key={value}
                      value={value}
                      className="h-10 flex-1 gap-2 rounded-full px-6 text-base text-gray-600 data-[state=active]:bg-white data-[state=active]:text-gray-900 sm:flex-none"
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      {label}
                      <span className="text-xs font-normal text-gray-400">
                        {countFor(value)}
                      </span>
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
              <MacBookPricesTable
                key={productLine}
                productLine={productLine}
                data={allPrices.filter(
                  (item) => (item.productLine || "mac") === productLine,
                )}
                currency={currency}
                posthog={posthog}
              />
            </>
          )}

          {/* Disclaimer */}
          <div className="mt-8 text-sm text-gray-600 text-left bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="font-semibold text-gray-900 mb-2">
              💡 Important Notes:
            </p>
            <ul className="space-y-2 list-disc list-inside">
              <li>
                <strong>VAT refund:</strong> foreign passport holders get back
                85% of the VAT when they fly out (the refunding bank keeps
                15%). VAT is {vatPercentOn()}%
                {vatPercentOn() === 8 && " until 31 Dec 2026, then 10%"}, so
                the refund is about{" "}
                {(refundShareOfPrice() * 100).toFixed(1)}% of the price. The
                Est. Price column already takes it off.
              </li>
              <li>
                <strong>To qualify:</strong> spend at least ₫2,000,000 at one
                shop in one day, at a branch registered for VAT refunds (ask
                before you pay), get an electronic VAT invoice ("hóa đơn điện
                tử GTGT"), and leave Vietnam within 60 days of the invoice.
              </li>
              <li>
                <strong>At the airport:</strong> keep the product unopened in
                your carry-on. Show it with the invoice to customs before
                check-in, at least 30 minutes before departure (arrive early).
                The refund is paid in VND at the refund counter after security,
                at international airports such as Hanoi, Ho Chi Minh City and
                Da Nang.
              </li>
              <li>
                <strong>Bargaining:</strong> prices shown are from online
                stores. Physical stores often allow 2-5% off, or 5-10% with
                skilled bargaining; the slider above applies it to the
                estimated price and refund.
              </li>
              <li>
                <strong>Price accuracy:</strong> prices are indicative and
                change often. Always confirm the price, and that the item is in
                stock rather than pre-order, at the store before buying.
              </li>
            </ul>
            <p className="mt-3 text-xs text-gray-500">
              VAT refund rules: Decree 181/2025/ND-CP and Circular
              84/2026/TT-BTC; 8% VAT rate: Decree 174/2025/ND-CP.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
