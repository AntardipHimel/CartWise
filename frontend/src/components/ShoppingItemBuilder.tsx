"use client";

import { useEffect, useMemo, useState } from "react";
import { getItemFilters, getItemSuggestions } from "@/lib/api";

type ItemFilters = {
  brand: string | null;
  package_size: number | null;
  package_unit: string | null;
  max_price: number | null;
  must_buy: boolean;
  allow_substitutes: boolean;
};

type ItemFilterOptions = {
  brands: string[];
  sizes: { package_size: number; package_unit: string; label: string }[];
};

export type DraftShoppingItem = {
  id: string;
  item_key: string;
  expanded: boolean;
  filters: ItemFilters;
  filterOptions: ItemFilterOptions;
};

type Props = {
  items: DraftShoppingItem[];
  setItems: React.Dispatch<React.SetStateAction<DraftShoppingItem[]>>;
};

const emptyOptions: ItemFilterOptions = {
  brands: [],
  sizes: [],
};

const defaultFilters: ItemFilters = {
  brand: null,
  package_size: null,
  package_unit: null,
  max_price: null,
  must_buy: true,
  allow_substitutes: true,
};

export default function ShoppingItemBuilder({ items, setItems }: Props) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setSuggestions([]);
      return;
    }

    const timeout = setTimeout(async () => {
      setLoadingSuggestions(true);
      try {
        const result = await getItemSuggestions(trimmed);
        setSuggestions(result?.suggestions ?? []);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 200);

    return () => clearTimeout(timeout);
  }, [query]);

  const selectedKeys = useMemo(() => new Set(items.map((item) => item.item_key)), [items]);

  const visibleSuggestions = useMemo(() => {
    return suggestions.filter((suggestion) => !selectedKeys.has(suggestion));
  }, [suggestions, selectedKeys]);

  const addItem = async (itemKey: string) => {
    if (!itemKey || selectedKeys.has(itemKey)) return;

    const filters = await getItemFilters(itemKey);

    setItems((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        item_key: itemKey,
        expanded: false,
        filters: { ...defaultFilters },
        filterOptions: {
          brands: filters?.brands ?? [],
          sizes: filters?.sizes ?? [],
        },
      },
    ]);
    setQuery("");
    setSuggestions([]);
  };

  const removeItem = (id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  const toggleExpanded = (id: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, expanded: !item.expanded } : item
      )
    );
  };

  const updateBrand = (id: string, value: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              filters: {
                ...item.filters,
                brand: value || null,
              },
            }
          : item
      )
    );
  };

  const updateSize = (id: string, value: string) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;
        if (!value) {
          return {
            ...item,
            filters: {
              ...item.filters,
              package_size: null,
              package_unit: null,
            },
          };
        }

        const [size, unit] = value.split("|");
        return {
          ...item,
          filters: {
            ...item.filters,
            package_size: Number(size),
            package_unit: unit,
          },
        };
      })
    );
  };

  const updateMaxPrice = (id: string, value: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              filters: {
                ...item.filters,
                max_price: value ? Number(value) : null,
              },
            }
          : item
      )
    );
  };

  const updateToggle = (
    id: string,
    key: "must_buy" | "allow_substitutes",
    value: boolean
  ) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              filters: {
                ...item.filters,
                [key]: value,
              },
            }
          : item
      )
    );
  };

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <h2 className="mb-4 text-xl font-semibold text-emerald-300">Shopping List</h2>

      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Start typing item name"
          className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
        />

        {(visibleSuggestions.length > 0 || loadingSuggestions) && query.trim() && (
          <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-gray-700 bg-gray-800 shadow-xl">
            {loadingSuggestions && (
              <div className="px-4 py-3 text-sm text-gray-400">Loading suggestions...</div>
            )}

            {!loadingSuggestions &&
              visibleSuggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => addItem(suggestion)}
                  className="block w-full px-4 py-3 text-left text-sm text-gray-200 transition hover:bg-gray-700"
                >
                  {suggestion}
                </button>
              ))}

            {!loadingSuggestions && visibleSuggestions.length === 0 && (
              <div className="px-4 py-3 text-sm text-gray-500">No matching items found.</div>
            )}
          </div>
        )}
      </div>

      <div className="mt-6 space-y-3">
        {items.length === 0 && (
          <div className="rounded-xl bg-gray-800 px-4 py-4 text-center text-gray-500">
            Select items from the suggestion list to build candidate products.
          </div>
        )}

        {items.map((item) => {
          const selectedSizeValue =
            item.filters.package_size !== null && item.filters.package_unit
              ? `${item.filters.package_size}|${item.filters.package_unit}`
              : "";

          return (
            <div key={item.id} className="rounded-xl border border-gray-800 bg-gray-800">
              <div className="flex items-center justify-between gap-3 px-4 py-4">
                <div>
                  <div className="font-medium text-white">{item.item_key}</div>
                  <div className="mt-1 text-sm text-gray-400">
                    {item.filters.brand || "Any brand"}
                    {" • "}
                    {item.filters.package_size && item.filters.package_unit
                      ? `${item.filters.package_size} ${item.filters.package_unit}`
                      : "Any size"}
                    {" • "}
                    {item.filters.max_price !== null
                      ? `Max $${item.filters.max_price.toFixed(2)}`
                      : "Any price"}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => toggleExpanded(item.id)}
                    className="rounded-xl border border-gray-700 px-3 py-2 text-sm font-medium text-gray-300 transition hover:border-emerald-500 hover:text-emerald-400"
                  >
                    {item.expanded ? "Hide Filters" : "Filters"}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeItem(item.id)}
                    className="rounded-xl border border-red-500/40 px-3 py-2 text-sm font-medium text-red-300 transition hover:bg-red-500/10"
                  >
                    Remove
                  </button>
                </div>
              </div>

              {item.expanded && (
                <div className="grid grid-cols-1 gap-4 border-t border-gray-700 px-4 py-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Brand</label>
                    <select
                      value={item.filters.brand ?? ""}
                      onChange={(event) => updateBrand(item.id, event.target.value)}
                      className="w-full rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    >
                      <option value="">Any brand</option>
                      {item.filterOptions.brands.map((brand) => (
                        <option key={brand} value={brand}>
                          {brand}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Size</label>
                    <select
                      value={selectedSizeValue}
                      onChange={(event) => updateSize(item.id, event.target.value)}
                      className="w-full rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    >
                      <option value="">Any size</option>
                      {item.filterOptions.sizes.map((size) => (
                        <option
                          key={`${size.package_size}-${size.package_unit}`}
                          value={`${size.package_size}|${size.package_unit}`}
                        >
                          {size.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Max price</label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.filters.max_price ?? ""}
                      onChange={(event) => updateMaxPrice(item.id, event.target.value)}
                      className="w-full rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                      placeholder="Optional"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <label className="flex items-center justify-between rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-sm text-gray-300">
                      Must buy
                      <input
                        type="checkbox"
                        checked={item.filters.must_buy}
                        onChange={(event) => updateToggle(item.id, "must_buy", event.target.checked)}
                        className="h-4 w-4 accent-emerald-500"
                      />
                    </label>

                    <label className="flex items-center justify-between rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-sm text-gray-300">
                      Allow substitutes
                      <input
                        type="checkbox"
                        checked={item.filters.allow_substitutes}
                        onChange={(event) =>
                          updateToggle(item.id, "allow_substitutes", event.target.checked)
                        }
                        className="h-4 w-4 accent-emerald-500"
                      />
                    </label>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}