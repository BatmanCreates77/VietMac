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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

const allColumns = [
  "Shop",
  "Model",
  "Configuration",
  "Category",
  "Status",
  "VND Price",
  "INR Price",
  "VAT Refund",
  "Final Price",
];

function MacBookPricesTable({ data }) {
  const [visibleColumns, setVisibleColumns] = useState([...allColumns]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortOrder, setSortOrder] = useState("default");
  const [isMobile, setIsMobile] = useState(false);

  const categories = ["All", "M4 Pro", "M4 Max", "M3 Max"];

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
    let filtered =
      selectedCategory === "All"
        ? data
        : data.filter((item) => item.category === selectedCategory);

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

  const toggleColumn = (col) => {
    setVisibleColumns((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col],
    );
  };

  return (
    <div className="container my-10 space-y-4 p-4 border border-border rounded-lg bg-background shadow-sm overflow-x-auto">
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between mb-6">
        {/* Category Filter Buttons */}
        <div className="flex flex-col gap-2 w-full md:w-auto">
          <div className="text-sm font-semibold text-gray-700">
            Filter by Chip:
          </div>
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Button
                key={category}
                onClick={() => setSelectedCategory(category)}
                size="sm"
                variant={selectedCategory === category ? "default" : "outline"}
                className={
                  selectedCategory === category
                    ? "bg-indigo-600 hover:bg-indigo-700"
                    : ""
                }
              >
                {category}
              </Button>
            ))}
          </div>
        </div>

        {/* Sort Buttons */}
        <div className="flex flex-col gap-2 w-full md:w-auto">
          <div className="text-sm font-semibold text-gray-700">
            Sort by Price:
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={() => setSortOrder("default")}
              size="sm"
              variant={sortOrder === "default" ? "default" : "outline"}
              className={
                sortOrder === "default"
                  ? "bg-indigo-600 hover:bg-indigo-700"
                  : ""
              }
            >
              Default
            </Button>
            <Button
              onClick={() => setSortOrder("low-to-high")}
              size="sm"
              variant={sortOrder === "low-to-high" ? "default" : "outline"}
              className={
                sortOrder === "low-to-high"
                  ? "bg-indigo-600 hover:bg-indigo-700"
                  : ""
              }
            >
              Low to High
            </Button>
            <Button
              onClick={() => setSortOrder("high-to-low")}
              size="sm"
              variant={sortOrder === "high-to-low" ? "default" : "outline"}
              className={
                sortOrder === "high-to-low"
                  ? "bg-indigo-600 hover:bg-indigo-700"
                  : ""
              }
            >
              High to Low
            </Button>
          </div>
        </div>

        {/* Column Visibility Toggle */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              Columns
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-48">
            {allColumns.map((col) => (
              <DropdownMenuCheckboxItem
                key={col}
                checked={visibleColumns.includes(col)}
                onCheckedChange={() => toggleColumn(col)}
              >
                {col}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Mobile Card View */}
      {isMobile ? (
        <div className="space-y-4">
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
                    <div className="flex gap-2">
                      <Badge variant="outline" className="w-fit">
                        {item.category}
                      </Badge>
                      <Badge
                        className={cn(
                          "w-fit",
                          item.available
                            ? "bg-green-100 text-green-700 border-green-200"
                            : "bg-red-100 text-red-700 border-red-200",
                        )}
                      >
                        {item.available ? "In Stock" : "Out of Stock"}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent">
                      ₹{item.finalPrice?.toLocaleString() || "N/A"}
                    </div>
                    <div className="text-xs font-medium text-gray-500">
                      Final Price
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
                      INR Price
                    </div>
                    <div className="font-bold text-blue-900">
                      ₹{item.inrPrice?.toLocaleString() || "N/A"}
                    </div>
                  </div>
                  <div className="bg-green-50/50 rounded-lg p-3 col-span-2">
                    <div className="text-gray-500 text-xs font-medium mb-1">
                      VAT Refund (8.5%)
                    </div>
                    <div className="font-bold text-green-600 text-lg">
                      -₹{item.vatRefund?.toLocaleString() || "N/A"}
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
            <TableRow>
              {visibleColumns.includes("Shop") && (
                <TableHead className="w-[150px]">Shop</TableHead>
              )}
              {visibleColumns.includes("Model") && (
                <TableHead className="w-[180px]">Model</TableHead>
              )}
              {visibleColumns.includes("Configuration") && (
                <TableHead className="w-[300px]">Configuration</TableHead>
              )}
              {visibleColumns.includes("Category") && (
                <TableHead className="w-[120px]">Category</TableHead>
              )}
              {visibleColumns.includes("Status") && (
                <TableHead className="w-[120px]">Status</TableHead>
              )}
              {visibleColumns.includes("VND Price") && (
                <TableHead className="w-[130px]">VND Price</TableHead>
              )}
              {visibleColumns.includes("INR Price") && (
                <TableHead className="w-[130px]">INR Price</TableHead>
              )}
              {visibleColumns.includes("VAT Refund") && (
                <TableHead className="w-[130px]">VAT Refund</TableHead>
              )}
              {visibleColumns.includes("Final Price") && (
                <TableHead className="w-[130px]">Final Price</TableHead>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.length ? (
              filteredData.map((item, idx) => (
                <TableRow
                  key={`${item.shop}-${item.id}-${idx}`}
                  className={cn(
                    "cursor-pointer hover:bg-gray-50/50",
                    getPriceHighlightClass(item.finalPrice),
                  )}
                  onClick={() =>
                    window.open(item.url, "_blank", "noopener,noreferrer")
                  }
                >
                  {visibleColumns.includes("Shop") && (
                    <TableCell className="font-medium whitespace-nowrap">
                      <Badge
                        className={cn(
                          "whitespace-nowrap",
                          item.shop === "FPT Shop" && "bg-blue-500 text-white",
                          item.shop === "ShopDunk" &&
                            "bg-purple-500 text-white",
                          item.shop === "TopZone" && "bg-green-500 text-white",
                          item.shop === "CellphoneS" &&
                            "bg-orange-500 text-white",
                        )}
                      >
                        {item.shop}
                      </Badge>
                    </TableCell>
                  )}
                  {visibleColumns.includes("Model") && (
                    <TableCell className="font-medium whitespace-nowrap">
                      {item.model}
                    </TableCell>
                  )}
                  {visibleColumns.includes("Configuration") && (
                    <TableCell className="whitespace-nowrap text-xs">
                      {item.configuration}
                    </TableCell>
                  )}
                  {visibleColumns.includes("Category") && (
                    <TableCell className="whitespace-nowrap">
                      <Badge variant="outline">{item.category}</Badge>
                    </TableCell>
                  )}
                  {visibleColumns.includes("Status") && (
                    <TableCell className="whitespace-nowrap">
                      <Badge
                        className={cn(
                          item.available
                            ? "bg-green-100 text-green-700 border-green-200"
                            : "bg-red-100 text-red-700 border-red-200",
                        )}
                      >
                        {item.available ? "In Stock" : "Out of Stock"}
                      </Badge>
                    </TableCell>
                  )}
                  {visibleColumns.includes("VND Price") && (
                    <TableCell className="whitespace-nowrap">
                      ₫{item.vndPrice?.toLocaleString() || "N/A"}
                    </TableCell>
                  )}
                  {visibleColumns.includes("INR Price") && (
                    <TableCell className="whitespace-nowrap">
                      ₹{item.inrPrice?.toLocaleString() || "N/A"}
                    </TableCell>
                  )}
                  {visibleColumns.includes("VAT Refund") && (
                    <TableCell className="whitespace-nowrap text-green-600">
                      -₹{item.vatRefund?.toLocaleString() || "N/A"}
                    </TableCell>
                  )}
                  {visibleColumns.includes("Final Price") && (
                    <TableCell className="whitespace-nowrap font-bold text-primary">
                      ₹{item.finalPrice?.toLocaleString() || "N/A"}
                    </TableCell>
                  )}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={visibleColumns.length}
                  className="text-center py-6"
                >
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
