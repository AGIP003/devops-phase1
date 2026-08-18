import { useEffect, useRef } from "react";
import { init, use } from "echarts/core";
import { BarChart, HeatmapChart, LineChart } from "echarts/charts";
import {
  AriaComponent,
  CalendarComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";

use([
  AriaComponent,
  BarChart,
  CalendarComponent,
  GridComponent,
  HeatmapChart,
  LegendComponent,
  LineChart,
  SVGRenderer,
  TooltipComponent,
  VisualMapComponent,
]);

function EChart({ option, ariaLabel, className = "" }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const chart = init(container, null, { renderer: "svg" });
    chart.setOption(option, { notMerge: true });

    const resize = () => chart.resize();
    const observer = typeof ResizeObserver === "undefined"
      ? null
      : new ResizeObserver(resize);

    observer?.observe(container);
    window.addEventListener("resize", resize);

    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [option]);

  return (
    <div
      ref={containerRef}
      className={`analytics-echart ${className}`.trim()}
      role="img"
      aria-label={ariaLabel}
    />
  );
}

export default EChart;
