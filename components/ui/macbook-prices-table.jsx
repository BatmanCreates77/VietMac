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

function MacBookPricesTable({ data, currency }) {
  const [selectedModel, setSelectedModel] = useState("All");
  const [selectedScreenSize, setSelectedScreenSize] = useState("All");
  const [selectedChipset, setSelectedChipset] = useState("All");
  const [sortOrder, setSortOrder] = useState("default");
  const [isMobile, setIsMobile] = useState(false);

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
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center p-4 bg-white border-b border-gray-200 justify-between">
        {/* Filter Dropdowns */}
        <div className="flex flex-col md:flex-row gap-3 w-full md:w-auto">
          <div className="flex flex-col gap-2">
            <div className="text-sm font-semibold text-gray-700">Model</div>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
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
            <div className="text-sm font-semibold text-gray-700">Chipset</div>
            <Select value={selectedChipset} onValueChange={setSelectedChipset}>
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
            <div className="text-sm font-semibold text-gray-700">Sort</div>
            <Select value={sortOrder} onValueChange={setSortOrder}>
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Sort by price" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default</SelectItem>
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
                  "block border-0 rounded-xl p-5 space-y-4 shadow-lg ring-1 ring-gray-200/50 hover:shadow-xl transition-all cursor-pointer",
                  getPriceHighlightClass(item.finalPrice) ||
                    "bg-white/95 backdrop-blur-md",
                )}
              >
                <div className="flex justify-between items-start">
                  <div className="flex flex-col gap-2">
                    <Badge
                      className={cn(
                        "w-fit",
                        item.shop === "FPT Shop" && "bg-blue-500 text-white",
                        item.shop === "ShopDunk" && "bg-purple-500 text-white",
                        item.shop === "TopZone" && "bg-green-500 text-white",
                        item.shop === "CellphoneS" &&
                          "bg-orange-500 text-white",
                      )}
                    >
                      {item.shop}
                    </Badge>
                    <Badge variant="outline" className="w-fit">
                      {item.category}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent">
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
                  <div className="bg-green-50/50 rounded-lg p-3 col-span-2">
                    <div className="text-gray-500 text-xs font-medium mb-1">
                      VAT Refund (8.5%)
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
                    "cursor-pointer hover:bg-gray-50 transition-colors border-b border-gray-100",
                    getPriceHighlightClass(item.finalPrice),
                  )}
                  onClick={() =>
                    window.open(item.url, "_blank", "noopener,noreferrer")
                  }
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
                <TableCell colSpan={7} className="text-center py-6">
                  No results found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

export default MacBookPricesTable;
