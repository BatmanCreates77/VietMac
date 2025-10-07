"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

function MacBookPricesTable({ data, currency, posthog }) {
  const [selectedModel, setSelectedModel] = useState("All");
  const [selectedScreenSize, setSelectedScreenSize] = useState("All");
  const [selectedChipset, setSelectedChipset] = useState("All");
  const [sortOrder, setSortOrder] = useState("low-to-high");
  const [isMobile, setIsMobile] = useState(false);
  const [bargainDiscount, setBargainDiscount] = useState(0); // 0-10% typical bargaining discount
  const [showBargainSlider, setShowBargainSlider] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const getCurrencySymbol = (currency) => {
    const symbols = {
      INR: "₹",
      USD: "$",
      EUR: "€",
    };
    return symbols[currency] || currency;
  };

  const models = ["All", "MacBook Air", "MacBook Pro"];
  const screenSizes = ["All", '13"', '14"', '15"', '16"'];
  const chipsets = ["All", "M2", "M3", "M4", "M4 Pro", "M4 Max", "M3 Max"];

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const filterAndSortData = () => {
    let filtered = data.filter((item) => {
      const modelMatch =
        selectedModel === "All" || item.modelType === selectedModel;
      const sizeMatch =
        selectedScreenSize === "All" || item.screenSize === selectedScreenSize;
      const chipMatch =
        selectedChipset === "All" || item.category === selectedChipset;
      return modelMatch && sizeMatch && chipMatch;
    });

    // Apply bargaining discount to prices
    filtered = filtered.map((item) => {
      if (!item.convertedPrice) return item;

      const discountAmount = item.convertedPrice * (bargainDiscount / 100);
      const bargainedPrice = item.convertedPrice - discountAmount;
      const vatRefund = ((bargainedPrice * 8.5) / 108.5) * 0.78; // Recalculate VAT on bargained price
      const finalPrice = bargainedPrice - vatRefund;

      return {
        ...item,
        bargainedPrice: Math.round(bargainedPrice),
        bargainDiscount: Math.round(discountAmount),
        vatRefund: Math.round(vatRefund),
        finalPrice: Math.round(finalPrice),
      };
    });

    if (sortOrder === "low-to-high") {
      filtered = [...filtered].sort(
        (a, b) => (a.finalPrice || 0) - (b.finalPrice || 0),
      );
    } else if (sortOrder === "high-to-low") {
      filtered = [...filtered].sort(
        (a, b) => (b.finalPrice || 0) - (a.finalPrice || 0),
      );
    }

    return filtered;
  };

  const filteredData = filterAndSortData();

  // Find min and max final prices
  const finalPrices = filteredData
    .map((item) => item.finalPrice)
    .filter((price) => price != null);
  const minPrice = Math.min(...finalPrices);
  const maxPrice = Math.max(...finalPrices);

  const getPriceHighlightClass = (finalPrice) => {
    if (!finalPrice || finalPrices.length === 0) return "";
    if (finalPrice === minPrice) return "bg-green-50";
    if (finalPrice === maxPrice) return "bg-red-50";
    return "";
  };

  return (
    <div className="bg-white rounded-lg shadow-table-shadow overflow-hidden">
      <div className="flex flex-col gap-4 p-4 bg-white border-b border-gray-200">
        {/* Bargaining Toggle */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">
              💰 Did you bargain at the store?
            </span>
            {showBargainSlider && bargainDiscount > 0 && (
              <Badge
                variant="outline"
                className="bg-yellow-100 text-yellow-800 border-yellow-300"
              >
                -{bargainDiscount}% OFF
              </Badge>
            )}
          </div>
          <button
            onClick={() => {
              const newState = !showBargainSlider;
              posthog?.capture("bargain_toggle_clicked", {
                enabled: newState,
              });
              setShowBargainSlider(newState);
              if (showBargainSlider) {
                setBargainDiscount(0);
              }
            }}
            className={cn(
              "relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 hover:scale-110",
              showBargainSlider ? "bg-blue-600" : "bg-gray-300",
            )}
          >
            <span
              className={cn(
                "inline-block h-4 w-4 transform rounded-full bg-white transition-all duration-300 shadow-md",
                showBargainSlider ? "translate-x-6" : "translate-x-1",
              )}
            />
          </button>
        </div>

        {/* Bargaining Discount Slider - Collapsible */}
        {showBargainSlider && (
          <div className="w-full bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-semibold text-gray-900">
                    Adjust Your Bargaining Discount
                  </span>
                </div>
                <p className="text-xs text-gray-600">
                  Typical discounts: 2-5% (average negotiation) or 5-10%
                  (skilled bargaining)
                </p>
              </div>
              <div className="flex items-center gap-4 md:min-w-[300px]">
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  value={bargainDiscount}
                  onChange={(e) =>
                    setBargainDiscount(parseFloat(e.target.value))
                  }
                  className="flex-1 h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="text-right min-w-[60px]">
                  <div className="text-lg font-bold text-blue-600">
                    {bargainDiscount}%
                  </div>
                  <div className="text-xs text-gray-500">discount</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filter Accordion - Mobile Only */}
        <div className="md:hidden border border-gray-200 rounded-lg overflow-hidden">
          {/* Accordion Header */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="w-full flex justify-between items-center p-4 bg-white hover:bg-gray-50 transition-colors"
          >
            <span className="text-sm font-semibold text-gray-700">Filters</span>
            {showFilters ? (
              <ChevronUp className="h-5 w-5 text-gray-600" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-600" />
            )}
          </button>

          {/* Accordion Content */}
          {showFilters && (
            <div className="p-4 bg-white border-t border-gray-200 animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                <div className="flex flex-col md:flex-row gap-3 w-full md:w-auto">
                  <div className="flex flex-col gap-2">
                    <div className="text-sm font-semibold text-gray-700">
                      Model
                    </div>
                    <Select
                      value={selectedModel}
                      onValueChange={setSelectedModel}
                    >
                      <SelectTrigger className="w-full md:w-[180px]">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {models.map((model) => (
                          <SelectItem key={model} value={model}>
                            {model}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex flex-col gap-2">
                    <div className="text-sm font-semibold text-gray-700">
                      Screen Size
                    </div>
                    <Select
                      value={selectedScreenSize}
                      onValueChange={setSelectedScreenSize}
                    >
                      <SelectTrigger className="w-full md:w-[140px]">
                        <SelectValue placeholder="Select size" />
                      </SelectTrigger>
                      <SelectContent>
                        {screenSizes.map((size) => (
                          <SelectItem key={size} value={size}>
                            {size}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex flex-col gap-2">
                    <div className="text-sm font-semibold text-gray-700">
                      Chipset
                    </div>
                    <Select
                      value={selectedChipset}
                      onValueChange={setSelectedChipset}
                    >
                      <SelectTrigger className="w-full md:w-[140px]">
                        <SelectValue placeholder="Select chip" />
                      </SelectTrigger>
                      <SelectContent>
                        {chipsets.map((chip) => (
                          <SelectItem key={chip} value={chip}>
                            {chip}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex gap-3 w-full md:w-auto">
                  {/* Sort Dropdown */}
                  <div className="flex flex-col gap-2 w-full md:w-auto">
                    <div className="text-sm font-semibold text-gray-700">
                      Sort
                    </div>
                    <Select value={sortOrder} onValueChange={setSortOrder}>
                      <SelectTrigger className="w-full md:w-[180px]">
                        <SelectValue placeholder="Sort by price" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low-to-high">
                          Price: Low to High
                        </SelectItem>
                        <SelectItem value="high-to-low">
                          Price: High to Low
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Filter Dropdowns - Desktop Only */}
        <div className="hidden md:flex flex-row gap-4 items-center justify-between">
          <div className="flex flex-row gap-3">
            <div className="flex flex-col gap-2">
              <div className="text-sm font-semibold text-gray-700">Model</div>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-2">
              <div className="text-sm font-semibold text-gray-700">
                Screen Size
              </div>
              <Select
                value={selectedScreenSize}
                onValueChange={setSelectedScreenSize}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Select size" />
                </SelectTrigger>
                <SelectContent>
                  {screenSizes.map((size) => (
                    <SelectItem key={size} value={size}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-2">
              <div className="text-sm font-semibold text-gray-700">Chipset</div>
              <Select
                value={selectedChipset}
                onValueChange={setSelectedChipset}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Select chip" />
                </SelectTrigger>
                <SelectContent>
                  {chipsets.map((chip) => (
                    <SelectItem key={chip} value={chip}>
                      {chip}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Sort Dropdown */}
          <div className="flex flex-col gap-2">
            <div className="text-sm font-semibold text-gray-700">Sort</div>
            <Select value={sortOrder} onValueChange={setSortOrder}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sort by price" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low-to-high">Price: Low to High</SelectItem>
                <SelectItem value="high-to-low">Price: High to Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Mobile Card View */}
      {isMobile ? (
        <div className="space-y-4 p-4">
          {filteredData.length ? (
            filteredData.map((item, idx) => (
              <a
                key={`${item.shop}-${item.id}-${idx}`}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  "block border-0 rounded-xl p-5 space-y-4 shadow-lg ring-1 ring-gray-200/50 hover:shadow-xl hover:scale-[1.02] hover:-translate-y-1 transition-all duration-300 cursor-pointer",
                  getPriceHighlightClass(item.finalPrice) ||
                    "bg-white/95 backdrop-blur-md",
                )}
              >
                <div className="flex justify-between items-start">
                  <div className="flex flex-col gap-2">
                    <Badge
                      className={cn(
                        "w-fit transition-all duration-200 hover:scale-105",
                        item.shop === "FPT Shop" && "bg-blue-500 text-white",
                        item.shop === "ShopDunk" && "bg-purple-500 text-white",
                        item.shop === "TopZone" && "bg-green-500 text-white",
                        item.shop === "CellphoneS" &&
                          "bg-orange-500 text-white",
                      )}
                    >
                      {item.shop}
                    </Badge>
                    <Badge
                      variant="outline"
                      className="w-fit transition-all duration-200 hover:scale-105"
                    >
                      {item.category}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent animate-in fade-in zoom-in-50 duration-500">
                      {getCurrencySymbol(currency)}
                      {item.finalPrice?.toLocaleString() || "N/A"}
                    </div>
                    <div className="text-xs font-medium text-gray-500">
                      Est. Price
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-200/50 pt-4">
                  <div className="font-semibold text-base text-gray-900">
                    {item.model}
                  </div>
                  <div className="text-sm text-gray-600 mt-1.5">
                    {item.configuration}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm border-t border-gray-200/50 pt-4">
                  <div className="bg-gray-50/50 rounded-lg p-3">
                    <div className="text-gray-500 text-xs font-medium mb-1">
                      VND Price
                    </div>
                    <div className="font-bold text-gray-900">
                      ₫{item.vndPrice?.toLocaleString() || "N/A"}
                    </div>
                  </div>
                  <div className="bg-blue-50/50 rounded-lg p-3">
                    <div className="text-gray-500 text-xs font-medium mb-1">
                      {currency} Price
                    </div>
                    <div className="font-bold text-blue-900">
                      {getCurrencySymbol(currency)}
                      {item.convertedPrice?.toLocaleString() || "N/A"}
                    </div>
                  </div>
                  {bargainDiscount > 0 && item.bargainDiscount && (
                    <div className="bg-yellow-50/50 rounded-lg p-3 col-span-2">
                      <div className="text-gray-500 text-xs font-medium mb-1">
                        Bargaining Discount ({bargainDiscount}%)
                      </div>
                      <div className="font-bold text-yellow-700">
                        -{getCurrencySymbol(currency)}
                        {item.bargainDiscount?.toLocaleString()}
                      </div>
                    </div>
                  )}
                  <div className="bg-green-50/50 rounded-lg p-3 col-span-2">
                    <div className="text-gray-500 text-xs font-medium mb-1">
                      VAT Refund (8.5% with fees)
                    </div>
                    <div className="font-bold text-green-600 text-lg">
                      -{getCurrencySymbol(currency)}
                      {item.vatRefund?.toLocaleString() || "N/A"}
                    </div>
                  </div>
                </div>
              </a>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              No results found.
            </div>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <Table className="w-full">
            <TableHeader>
              <TableRow className="border-b border-gray-200 bg-white hover:bg-white">
                <TableHead className="w-[150px] text-gray-900 font-semibold">
                  Shop
                </TableHead>
                <TableHead className="w-[180px] text-gray-900 font-semibold">
                  Model
                </TableHead>
                <TableHead className="w-[400px] text-gray-900 font-semibold">
                  Config
                </TableHead>
                <TableHead className="w-[130px] text-gray-900 font-semibold">
                  VND Price
                </TableHead>
                <TableHead className="w-[130px] text-gray-900 font-semibold">
                  {currency} Price
                </TableHead>
                {bargainDiscount > 0 && (
                  <TableHead className="w-[130px] text-yellow-700 font-semibold">
                    Bargain -{bargainDiscount}%
                  </TableHead>
                )}
                <TableHead className="w-[130px] text-gray-900 font-semibold">
                  VAT Refund
                </TableHead>
                <TableHead className="w-[130px] text-gray-900 font-semibold">
                  Est. Price
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.length ? (
                filteredData.map((item, idx) => (
                  <TableRow
                    key={`${item.shop}-${item.id}-${idx}`}
                    className={cn(
                      "cursor-pointer hover:bg-gray-50 hover:shadow-md transition-all duration-200 border-b border-gray-100",
                      getPriceHighlightClass(item.finalPrice),
                    )}
                    onClick={() => {
                      posthog?.capture("macbook_listing_clicked", {
                        shop: item.shop,
                        model: item.model,
                        category: item.category,
                        price_vnd: item.vndPrice,
                        final_price: item.finalPrice,
                        currency: currency,
                      });
                      window.open(item.url, "_blank", "noopener,noreferrer");
                    }}
                  >
                    <TableCell className="font-medium whitespace-nowrap text-gray-900">
                      {item.shop}
                    </TableCell>
                    <TableCell className="font-medium whitespace-nowrap text-gray-900">
                      {item.model}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-sm text-gray-700">
                      {item.configuration}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-gray-900">
                      ₫{item.vndPrice?.toLocaleString() || "N/A"}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-gray-900">
                      {getCurrencySymbol(currency)}
                      {item.convertedPrice?.toLocaleString() || "N/A"}
                    </TableCell>
                    {bargainDiscount > 0 && (
                      <TableCell className="whitespace-nowrap text-yellow-700 font-medium">
                        -{getCurrencySymbol(currency)}
                        {item.bargainDiscount?.toLocaleString() || "N/A"}
                      </TableCell>
                    )}
                    <TableCell className="whitespace-nowrap text-green-600 font-medium">
                      -{getCurrencySymbol(currency)}
                      {item.vatRefund?.toLocaleString() || "N/A"}
                    </TableCell>
                    <TableCell className="whitespace-nowrap font-bold text-gray-900">
                      {getCurrencySymbol(currency)}
                      {item.finalPrice?.toLocaleString() || "N/A"}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={bargainDiscount > 0 ? 8 : 7}
                    className="text-center py-6"
                  >
                    No results found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

export default MacBookPricesTable;
