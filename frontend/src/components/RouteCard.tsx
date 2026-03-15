import React, { useState, useMemo, useEffect } from "react";
import type {
  MultiRouteResponse,
  RouteCard,
  RouteStop,
  RouteProduct,
} from "@/types/routes";

/* ═══════════════════════════════════════════════════════════
 * Props
 * ═══════════════════════════════════════════════════════════ */

export interface RouteCardsProps {
  /** Live API response — null while loading or before first fetch */
  data: MultiRouteResponse | null;
  /** Show skeleton cards while fetching */
  loading?: boolean;
  /** Error message to display */
  error?: string | null;
  /** HH:MM string shown in the Start waypoint */
  tripStartTime?: string;
  /** Lift time changes up to parent */
  onTripStartChange?: (time: string) => void;
  /** Lift route selection up to parent */
  onSelectRoute?: (rank: number) => void;
}

type FilterKey = "all" | "balanced" | "single" | "multi";

/* ── Inline SVG icons ── */

const ChevronDown: React.FC<{ open: boolean }> = ({ open }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{
      transform: open ? "rotate(180deg)" : "rotate(0)",
      transition: "transform 0.25s ease",
    }}
  >
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

const MapPinIcon: React.FC = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
    <circle cx="12" cy="10" r="3" />
  </svg>
);

const StoreIcon: React.FC = () => (
  <svg
    width="15"
    height="15"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
);

const CheckCircle: React.FC = () => (
  <svg
    width="15"
    height="15"
    viewBox="0 0 24 24"
    fill="none"
    stroke="#16a34a"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const StarIcon: React.FC = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="#f59e0b"
    stroke="#f59e0b"
    strokeWidth="1"
  >
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);

/* ── Helpers ── */

const fmtTime = (min: number | null | undefined): string => {
  if (min == null) return "—";
  if (min < 60) return `${Math.round(min)} min`;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
};

const fmtMiles = (mi: number | null | undefined): string =>
  mi != null ? `${Number(mi).toFixed(1)} mi` : "—";

const fmtPrice = (p: number | null | undefined): string =>
  p != null ? `$${Number(p).toFixed(2)}` : "—";

const STORE_COLORS: string[] = [
  "#2563eb", "#d946ef", "#ea580c", "#0d9488", "#7c3aed",
  "#dc2626", "#0284c7", "#ca8a04", "#4f46e5", "#059669",
];

const getStoreColor = (idx: number): string =>
  STORE_COLORS[idx % STORE_COLORS.length];

/* ══════════════════════════════════════════════════════════
 * Sub-components
 * ══════════════════════════════════════════════════════════ */

/* ── Product row ── */

interface ProductRowProps {
  product: RouteProduct;
  idx: number;
}

const ProductRow: React.FC<ProductRowProps> = ({ product, idx }) => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "22px 1fr 1fr 0.7fr 0.8fr",
      gap: "6px",
      alignItems: "center",
      padding: "6px 0",
      fontSize: "12.5px",
      color: "var(--cw-text)",
      borderBottom: "1px solid var(--cw-border-light)",
    }}
  >
    <span style={{ color: "var(--cw-text-dim)", fontVariantNumeric: "tabular-nums" }}>
      {idx + 1}.
    </span>
    <span
      style={{
        fontWeight: 500,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
    >
      {product.item_name}
      {product.on_sale && (
        <span
          style={{
            marginLeft: 4,
            fontSize: 10,
            background: "#fef3c7",
            color: "#92400e",
            borderRadius: 3,
            padding: "1px 4px",
            fontWeight: 600,
          }}
        >
          SALE
        </span>
      )}
    </span>
    <span style={{ color: "var(--cw-text-dim)" }}>{product.brand || "—"}</span>
    <span style={{ color: "var(--cw-text-dim)", fontSize: 11 }}>
      {product.unit_size ? `${product.unit_size}${product.unit_type || ""}` : "—"}
    </span>
    <span
      style={{
        fontWeight: 600,
        textAlign: "right",
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {fmtPrice(product.price)}
    </span>
  </div>
);

/* ── Store stop with expandable products ── */

interface StoreStopProps {
  stop: RouteStop;
  storeIdx: number;
  isLast: boolean;
}

const StoreStop: React.FC<StoreStopProps> = ({ stop, storeIdx, isLast }) => {
  const [open, setOpen] = useState<boolean>(false);
  const color = getStoreColor(storeIdx);
  const products = stop.products || [];
  const productTotal = products.reduce((s, p) => s + (p.price || 0), 0);

  return (
    <div style={{ position: "relative", paddingLeft: 28 }}>
      {!isLast && (
        <div
          style={{
            position: "absolute",
            left: 10,
            top: 22,
            bottom: 0,
            width: 2,
            background: "var(--cw-border)",
          }}
        />
      )}
      <div
        style={{
          position: "absolute",
          left: 4,
          top: 6,
          width: 14,
          height: 14,
          borderRadius: "50%",
          background: color,
          border: "2.5px solid white",
          boxShadow: `0 0 0 1px ${color}`,
        }}
      />

      <div
        style={{
          background: "var(--cw-card-inner)",
          border: "1px solid var(--cw-border)",
          borderRadius: 8,
          marginBottom: 8,
          overflow: "hidden",
        }}
      >
        <button
          onClick={() => setOpen(!open)}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px 12px",
            background: "none",
            border: "none",
            cursor: "pointer",
            gap: 8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
            <StoreIcon />
            <span
              style={{
                fontWeight: 600,
                fontSize: 13,
                color: "var(--cw-text)",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {stop.label}
            </span>
            <span style={{ fontSize: 11, color: "var(--cw-text-dim)", flexShrink: 0 }}>
              {products.length} items
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              flexShrink: 0,
              fontSize: 12,
            }}
          >
            <span style={{ color: "var(--cw-text-dim)" }}>
              +{fmtMiles(stop.distance_from_prev)}
            </span>
            <span style={{ color: "var(--cw-text-dim)" }}>
              {fmtTime(stop.cumulative_time_minutes)}
            </span>
            <span
              style={{
                fontWeight: 600,
                color: "var(--cw-text)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {fmtPrice(productTotal)}
            </span>
            <ChevronDown open={open} />
          </div>
        </button>

        {open && (
          <div
            style={{
              padding: "0 12px 10px 12px",
              borderTop: "1px solid var(--cw-border-light)",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "22px 1fr 1fr 0.7fr 0.8fr",
                gap: "6px",
                padding: "8px 0 4px",
                fontSize: "10.5px",
                fontWeight: 600,
                color: "var(--cw-text-dim)",
                textTransform: "uppercase",
                letterSpacing: "0.04em",
              }}
            >
              <span>#</span>
              <span>Name</span>
              <span>Brand</span>
              <span>Size</span>
              <span style={{ textAlign: "right" }}>Price</span>
            </div>
            {products.map((p, i) => (
              <ProductRow key={i} product={p} idx={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/* ── Waypoint (start / end) ── */

interface WaypointProps {
  stop: RouteStop;
  type: "start" | "end";
  isLast: boolean;
  tripStartTime?: string;
}

const Waypoint: React.FC<WaypointProps> = ({ stop, type, isLast, tripStartTime }) => {
  const isStart = type === "start";
  return (
    <div style={{ position: "relative", paddingLeft: 28, marginBottom: 8 }}>
      {!isLast && (
        <div
          style={{
            position: "absolute",
            left: 10,
            top: 22,
            bottom: 0,
            width: 2,
            background: "var(--cw-border)",
          }}
        />
      )}
      <div
        style={{
          position: "absolute",
          left: 4,
          top: 6,
          width: 14,
          height: 14,
          borderRadius: "50%",
          background: isStart ? "#16a34a" : "#dc2626",
          border: "2.5px solid white",
          boxShadow: `0 0 0 1px ${isStart ? "#16a34a" : "#dc2626"}`,
        }}
      />
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 12px",
          background: "var(--cw-card-inner)",
          border: "1px solid var(--cw-border)",
          borderRadius: 8,
          fontSize: 13,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <MapPinIcon />
          <span style={{ fontWeight: 600, color: "var(--cw-text)" }}>{stop.label}</span>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            fontSize: 12,
            color: "var(--cw-text-dim)",
          }}
        >
          {isStart ? (
            <>
              <span>Distance: 0</span>
              <span>Time: {tripStartTime || "—"}</span>
            </>
          ) : (
            <>
              <span>+{fmtMiles(stop.distance_from_prev)}</span>
              <span>{fmtTime(stop.cumulative_time_minutes)}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

/* ── Trip plan accordion ── */

interface TripPlanProps {
  stops: RouteStop[];
  tripStartTime?: string;
}

const TripPlan: React.FC<TripPlanProps> = ({ stops, tripStartTime }) => {
  const [open, setOpen] = useState<boolean>(false);
  const safeStops = stops || [];
  const storeStops = safeStops.filter((s) => s.type === "store");

  return (
    <div style={{ borderTop: "1px solid var(--cw-border)" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "11px 16px",
          background: "none",
          border: "none",
          cursor: "pointer",
        }}
      >
        <span
          style={{
            fontWeight: 600,
            fontSize: 13.5,
            color: "var(--cw-text)",
            letterSpacing: "-0.01em",
          }}
        >
          Trip Plan
        </span>
        <ChevronDown open={open} />
      </button>

      {open && (
        <div style={{ padding: "4px 16px 16px" }}>
          {safeStops.map((stop, i) => {
            if (stop.type === "start") {
              return (
                <Waypoint
                  key={i}
                  stop={stop}
                  type="start"
                  isLast={i === safeStops.length - 1}
                  tripStartTime={tripStartTime}
                />
              );
            }
            if (stop.type === "end") {
              return <Waypoint key={i} stop={stop} type="end" isLast />;
            }
            const storeIdx = storeStops.indexOf(stop);
            return (
              <StoreStop
                key={i}
                stop={stop}
                storeIdx={storeIdx}
                isLast={i === safeStops.length - 1}
              />
            );
          })}

          <div
            style={{
              marginTop: 12,
              padding: "18px 16px",
              background: "linear-gradient(135deg, var(--cw-card-inner), var(--cw-bg))",
              border: "1px dashed var(--cw-border)",
              borderRadius: 8,
              textAlign: "center",
              fontSize: 12.5,
              color: "var(--cw-text-dim)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
            }}
          >
            <MapPinIcon /> Map for this Trip
          </div>
        </div>
      )}
    </div>
  );
};

/* ── Metric pill ── */

interface PillProps {
  label: string;
  value: string | number;
  accent?: boolean;
}

const Pill: React.FC<PillProps> = ({ label, value, accent }) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 2,
      padding: "6px 10px",
      background: accent ? "var(--cw-accent-bg)" : "var(--cw-card-inner)",
      borderRadius: 6,
      border: `1px solid ${accent ? "var(--cw-accent-border)" : "var(--cw-border-light)"}`,
      minWidth: 72,
    }}
  >
    <span
      style={{
        fontSize: 10,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        color: accent ? "var(--cw-accent)" : "var(--cw-text-dim)",
      }}
    >
      {label}
    </span>
    <span
      style={{
        fontSize: 14,
        fontWeight: 700,
        color: accent ? "var(--cw-accent)" : "var(--cw-text)",
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {value}
    </span>
  </div>
);

/* ── Single route card ── */

interface RouteCardUIProps {
  route: RouteCard;
  isSelected: boolean;
  onSelect: (rank: number) => void;
  tripStartTime?: string;
}

const RouteCardUI: React.FC<RouteCardUIProps> = ({
  route,
  isSelected,
  onSelect,
  tripStartTime,
}) => (
  <div
    style={{
      background: "var(--cw-card)",
      border: isSelected
        ? "2px solid var(--cw-accent)"
        : "1px solid var(--cw-border)",
      borderRadius: 12,
      overflow: "hidden",
      boxShadow: isSelected
        ? "0 0 0 3px var(--cw-accent-bg)"
        : "0 1px 3px rgba(0,0,0,0.06)",
      transition: "border-color 0.2s, box-shadow 0.2s",
    }}
  >
    {/* Header */}
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 16px",
        background: route.is_balanced_pick
          ? "linear-gradient(135deg, #fffbeb, #fef3c7)"
          : "transparent",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            fontWeight: 700,
            fontSize: 15,
            color: "var(--cw-text)",
            letterSpacing: "-0.02em",
          }}
        >
          {route.label}
        </span>
        {route.is_balanced_pick && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 3,
              fontSize: 10.5,
              fontWeight: 700,
              color: "#92400e",
              background: "#fde68a",
              borderRadius: 4,
              padding: "2px 7px",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            <StarIcon /> Best Balanced
          </span>
        )}
        {route.rank === 1 && !route.is_balanced_pick && (
          <span
            style={{
              fontSize: 10.5,
              fontWeight: 700,
              color: "#166534",
              background: "#dcfce7",
              borderRadius: 4,
              padding: "2px 7px",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            Cheapest
          </span>
        )}
      </div>
      <button
        onClick={() => onSelect(route.rank)}
        style={{
          padding: "6px 14px",
          fontSize: 12,
          fontWeight: 600,
          borderRadius: 6,
          border: isSelected ? "none" : "1px solid var(--cw-border)",
          background: isSelected ? "var(--cw-accent)" : "var(--cw-card)",
          color: isSelected ? "white" : "var(--cw-text)",
          cursor: "pointer",
          transition: "all 0.15s ease",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        {isSelected && <CheckCircle />}
        {isSelected ? "Selected" : "Select Route"}
      </button>
    </div>

    {/* Metrics bar */}
    <div style={{ display: "flex", gap: 8, padding: "8px 16px 12px", flexWrap: "wrap" }}>
      <Pill label="Total Cost" value={fmtPrice(route.total_cost)} accent />
      <Pill label="Travel" value={fmtMiles(route.travel_distance_miles)} />
      <Pill
        label="Items"
        value={`${route.items_included}/${route.items_included + route.items_missing}`}
      />
      <Pill label="Stores" value={route.store_count} />
    </div>

    {/* Trip plan accordion */}
    <TripPlan stops={route.stops} tripStartTime={tripStartTime} />
  </div>
);

/* ═══════════════════════════════════════════════════════════
 * RouteCards — main exported component
 * ═══════════════════════════════════════════════════════════ */

const RouteCards: React.FC<RouteCardsProps> = ({
  data,
  loading = false,
  error = null,
  tripStartTime = "10:00",
  onTripStartChange: _onTripStartChange,
  onSelectRoute,
}) => {
  const [selectedRoute, setSelectedRoute] = useState<number | null>(null);
  const [filter, setFilter] = useState<FilterKey>("all");

  // Auto-select balanced route when data arrives
  useEffect(() => {
    if (data?.balanced_route_rank && selectedRoute == null) {
      setSelectedRoute(data.balanced_route_rank);
      onSelectRoute?.(data.balanced_route_rank);
    }
  }, [data?.balanced_route_rank]); // eslint-disable-line react-hooks/exhaustive-deps

  const routes: RouteCard[] = data?.routes ?? [];

  const filteredRoutes = useMemo<RouteCard[]>(() => {
    switch (filter) {
      case "balanced":
        return routes.filter((r) => r.is_balanced_pick);
      case "single":
        return routes.filter((r) => r.store_count === 1);
      case "multi":
        return routes.filter((r) => r.store_count > 1);
      default:
        return routes;
    }
  }, [routes, filter]);

  const handleSelect = (rank: number): void => {
    setSelectedRoute(rank);
    onSelectRoute?.(rank);
  };

  /* ── Loading skeleton ── */
  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              background: "var(--cw-card, #fff)",
              border: "1px solid var(--cw-border, #e4e4e7)",
              borderRadius: 12,
              padding: 20,
              height: 120,
            }}
          >
            <div
              style={{
                width: "40%",
                height: 16,
                background: "#e5e7eb",
                borderRadius: 4,
                marginBottom: 12,
              }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              {[1, 2, 3, 4].map((j) => (
                <div
                  key={j}
                  style={{
                    width: 80,
                    height: 44,
                    background: "#f3f4f6",
                    borderRadius: 6,
                  }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div
        style={{
          background: "#fef2f2",
          border: "1px solid #fecaca",
          borderRadius: 10,
          padding: "14px 16px",
          fontSize: 13,
          color: "#991b1b",
          lineHeight: 1.5,
        }}
      >
        <strong>Error loading routes:</strong> {error}
      </div>
    );
  }

  /* ── Empty state ── */
  if (!data || routes.length === 0) {
    return (
      <div
        style={{
          textAlign: "center",
          padding: 40,
          color: "var(--cw-text-dim, #71717a)",
          fontSize: 14,
        }}
      >
        No routes available. Add items to your shopping list and try again.
      </div>
    );
  }

  const FILTERS: { key: FilterKey; label: string }[] = [
    { key: "all", label: "All Routes" },
    { key: "balanced", label: "Best Balanced" },
    { key: "single", label: "Single Store" },
    { key: "multi", label: "Multi Store" },
  ];

  return (
    <div>
      {/* Recommendation banner */}
      {data.recommendation_reason && (
        <div
          style={{
            background: "linear-gradient(135deg, #eff6ff, #dbeafe)",
            border: "1px solid #bfdbfe",
            borderRadius: 10,
            padding: "12px 16px",
            marginBottom: 16,
            fontSize: 13,
            color: "#1e40af",
            lineHeight: 1.5,
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
          }}
        >
          <span style={{ flexShrink: 0, marginTop: 1 }}>
            <StarIcon />
          </span>
          <span>{data.recommendation_reason}</span>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            style={{
              padding: "6px 14px",
              fontSize: 12,
              fontWeight: 600,
              borderRadius: 20,
              border:
                filter === f.key
                  ? "1.5px solid var(--cw-accent, #2563eb)"
                  : "1px solid var(--cw-border, #e4e4e7)",
              background:
                filter === f.key
                  ? "var(--cw-accent-bg, #eff6ff)"
                  : "white",
              color:
                filter === f.key
                  ? "var(--cw-accent, #2563eb)"
                  : "var(--cw-text-dim, #71717a)",
              cursor: "pointer",
              transition: "all 0.15s",
              fontFamily: "inherit",
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Route count */}
      <div
        style={{
          fontSize: 12,
          color: "var(--cw-text-dim, #71717a)",
          marginBottom: 12,
          fontWeight: 500,
        }}
      >
        Showing {filteredRoutes.length} of {routes.length} routes — sorted by
        total cost (cheapest first)
      </div>

      {/* Route cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {filteredRoutes.map((route) => (
          <RouteCardUI
            key={route.rank}
            route={route}
            isSelected={selectedRoute === route.rank}
            onSelect={handleSelect}
            tripStartTime={tripStartTime}
          />
        ))}
      </div>

      {filteredRoutes.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: 40,
            color: "var(--cw-text-dim, #71717a)",
            fontSize: 14,
          }}
        >
          No routes match the current filter.
        </div>
      )}
    </div>
  );
};

export default RouteCards;