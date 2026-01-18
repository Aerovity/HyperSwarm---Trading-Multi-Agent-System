"use client"

import { useEffect, useRef, memo } from "react"
import { createChart, IChartApi, ISeriesApi, ColorType, CandlestickSeries, LineSeries } from "lightweight-charts"
import { useTheme, Theme } from "@/lib/theme-context"
import { generateMockCandlestickData, generateNewCandle } from "@/lib/mock-data"

interface TradingChartProps {
  pair: string
  chartType?: "candlestick" | "line"
}

// Theme color mappings for Lightweight Charts
const chartThemes: Record<Theme, {
  background: string
  textColor: string
  gridColor: string
  upColor: string
  downColor: string
  wickUpColor: string
  wickDownColor: string
}> = {
  dark: {
    background: "#0A0A0A",
    textColor: "#8E8E93",
    gridColor: "rgba(255, 255, 255, 0.03)",
    upColor: "#30D158",
    downColor: "#FF453A",
    wickUpColor: "#30D158",
    wickDownColor: "#FF453A",
  },
  light: {
    background: "#F7F7F7",
    textColor: "#1d1d1f",
    gridColor: "rgba(0, 0, 0, 0.05)",
    upColor: "#34C759",
    downColor: "#FF3B30",
    wickUpColor: "#34C759",
    wickDownColor: "#FF3B30",
  },
  neon: {
    background: "#0a0a14",
    textColor: "#00ffff",
    gridColor: "rgba(0, 255, 255, 0.05)",
    upColor: "#00ff64",
    downColor: "#ff0055",
    wickUpColor: "#00ff64",
    wickDownColor: "#ff0055",
  },
  retro: {
    background: "#1a0a2e",
    textColor: "#ffd700",
    gridColor: "rgba(255, 215, 0, 0.05)",
    upColor: "#00ff88",
    downColor: "#ff6b6b",
    wickUpColor: "#00ff88",
    wickDownColor: "#ff6b6b",
  },
}

function TradingChartComponent({ pair, chartType = "candlestick" }: TradingChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | ISeriesApi<"Line"> | null>(null)
  const { theme } = useTheme()

  // Initialize chart
  useEffect(() => {
    if (!containerRef.current) return

    const colors = chartThemes[theme]

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: colors.background },
        textColor: colors.textColor,
      },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: colors.gridColor,
      },
      rightPriceScale: {
        borderColor: colors.gridColor,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          labelBackgroundColor: colors.upColor,
        },
        horzLine: {
          labelBackgroundColor: colors.upColor,
        },
      },
    })

    chartRef.current = chart

    // Create series based on chart type - using v5 API
    if (chartType === "candlestick") {
      seriesRef.current = chart.addSeries(CandlestickSeries, {
        upColor: colors.upColor,
        downColor: colors.downColor,
        wickUpColor: colors.wickUpColor,
        wickDownColor: colors.wickDownColor,
        borderVisible: false,
      })
    } else {
      seriesRef.current = chart.addSeries(LineSeries, {
        color: colors.upColor,
        lineWidth: 2,
      })
    }

    // Set initial mock data
    const mockData = generateMockCandlestickData(pair, 100)
    seriesRef.current.setData(mockData)
    chart.timeScale().fitContent()

    // Handle resize
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener("resize", handleResize)

    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(containerRef.current)

    return () => {
      window.removeEventListener("resize", handleResize)
      resizeObserver.disconnect()
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, [theme, chartType, pair])

  // Live data update simulation
  useEffect(() => {
    const interval = setInterval(() => {
      if (seriesRef.current && chartType === "candlestick") {
        const lastCandle = generateNewCandle(pair)
        ;(seriesRef.current as ISeriesApi<"Candlestick">).update(lastCandle)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [chartType, pair])

  return (
    <div ref={containerRef} className="w-full h-full min-h-[300px]" />
  )
}

export const TradingChart = memo(TradingChartComponent)
