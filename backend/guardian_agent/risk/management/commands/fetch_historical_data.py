"""
Django management command to fetch historical BTC/USD data from Hyperliquid.

Usage:
    uv run python manage.py fetch_historical_data --pair BTCUSD --timeframe 5m --days 365
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
import pandas as pd
import requests


class Command(BaseCommand):
    help = "Fetch historical OHLCV data from Hyperliquid for RL training"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pair",
            type=str,
            default="BTCUSD",
            help="Trading pair (default: BTCUSD)",
        )
        parser.add_argument(
            "--timeframe",
            type=str,
            default="5m",
            choices=["1m", "5m", "15m", "1h", "4h", "1d"],
            help="Candle timeframe (default: 5m)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="Number of days of history (default: 365)",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="./data/historical",
            help="Output directory (default: ./data/historical)",
        )
        parser.add_argument(
            "--format",
            type=str,
            default="parquet",
            choices=["parquet", "csv"],
            help="Output format (default: parquet)",
        )

    def handle(self, *args, **options):
        pair = options["pair"]
        timeframe = options["timeframe"]
        days = options["days"]
        output_dir = Path(options["output"])
        output_format = options["format"]

        output_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f"Fetching {days} days of {pair} {timeframe} data...")

        try:
            df = self.fetch_data(pair, timeframe, days)

            # Save data
            filename = f"{pair.lower()}_{timeframe}.{output_format}"
            filepath = output_dir / filename

            if output_format == "parquet":
                df.to_parquet(filepath, index=False)
            else:
                df.to_csv(filepath, index=False)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully saved {len(df)} candles to {filepath}"
                )
            )

            # Print summary
            self.stdout.write(f"\nData Summary:")
            self.stdout.write(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            self.stdout.write(f"  Candles: {len(df)}")
            self.stdout.write(f"  Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")

        except Exception as e:
            raise CommandError(f"Failed to fetch data: {e}")

    def fetch_data(self, pair: str, timeframe: str, days: int) -> pd.DataFrame:
        """
        Fetch historical data from Hyperliquid or fallback to demo data.
        """
        # Map timeframe to milliseconds
        tf_ms = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
        }

        interval_ms = tf_ms.get(timeframe, 5 * 60 * 1000)

        # Calculate time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)

        # Try Hyperliquid API first
        try:
            return self._fetch_from_hyperliquid(pair, interval_ms, start_time, end_time)
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Hyperliquid API failed: {e}")
            )
            self.stdout.write("Falling back to CryptoCompare API...")

        # Fallback to CryptoCompare (free tier)
        try:
            return self._fetch_from_cryptocompare(pair, timeframe, days)
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"CryptoCompare failed: {e}")
            )
            self.stdout.write("Generating synthetic demo data...")

        # Final fallback: generate demo data
        return self._generate_demo_data(pair, timeframe, days)

    def _fetch_from_hyperliquid(
        self, pair: str, interval_ms: int, start_time: int, end_time: int
    ) -> pd.DataFrame:
        """Fetch from Hyperliquid API."""
        # Hyperliquid candle endpoint
        url = "https://api.hyperliquid.xyz/info"

        # Map pair to Hyperliquid symbol
        symbol = "BTC" if "BTC" in pair.upper() else pair.replace("USD", "").replace("USDT", "")

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": str(interval_ms // (60 * 1000)) + "m",  # Convert to minutes
                "startTime": start_time,
                "endTime": end_time,
            }
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError("No data returned from Hyperliquid")

        # Parse response
        candles = []
        for candle in data:
            candles.append({
                "timestamp": pd.to_datetime(candle["t"], unit="ms"),
                "open": float(candle["o"]),
                "high": float(candle["h"]),
                "low": float(candle["l"]),
                "close": float(candle["c"]),
                "volume": float(candle["v"]),
            })

        return pd.DataFrame(candles)

    def _fetch_from_cryptocompare(
        self, pair: str, timeframe: str, days: int
    ) -> pd.DataFrame:
        """Fetch from CryptoCompare API (free tier)."""
        # Determine endpoint based on timeframe
        if timeframe in ["1m", "5m", "15m"]:
            endpoint = "histominute"
            limit = min(2000, days * 24 * 60 // int(timeframe.replace("m", "")))
            aggregate = int(timeframe.replace("m", ""))
        elif timeframe in ["1h", "4h"]:
            endpoint = "histohour"
            limit = min(2000, days * 24 // int(timeframe.replace("h", "")))
            aggregate = int(timeframe.replace("h", ""))
        else:  # 1d
            endpoint = "histoday"
            limit = min(2000, days)
            aggregate = 1

        url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}"
        params = {
            "fsym": "BTC",
            "tsym": "USD",
            "limit": limit,
            "aggregate": aggregate,
        }

        all_candles = []
        to_ts = None

        while len(all_candles) < days * 24 * 60 // max(1, int(timeframe.replace("m", "").replace("h", "").replace("d", "") or 1)):
            if to_ts:
                params["toTs"] = to_ts

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("Response") != "Success":
                raise ValueError(data.get("Message", "Unknown error"))

            candles = data.get("Data", {}).get("Data", [])
            if not candles:
                break

            all_candles.extend(candles)
            to_ts = candles[0]["time"] - 1

            if len(candles) < limit:
                break

            time.sleep(0.1)  # Rate limit

        # Convert to DataFrame
        df = pd.DataFrame(all_candles)
        df["timestamp"] = pd.to_datetime(df["time"], unit="s")
        df = df.rename(columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volumefrom": "volume",
        })
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("timestamp").drop_duplicates().reset_index(drop=True)

        return df

    def _generate_demo_data(
        self, pair: str, timeframe: str, days: int
    ) -> pd.DataFrame:
        """Generate synthetic demo data for testing."""
        import numpy as np

        self.stdout.write(self.style.WARNING("Generating synthetic demo data..."))

        # Calculate number of candles
        tf_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440
        }
        minutes = tf_minutes.get(timeframe, 5)
        num_candles = days * 24 * 60 // minutes

        # Generate realistic BTC price movements
        np.random.seed(42)

        # Start price around current BTC levels
        start_price = 45000

        # Generate log returns with realistic volatility
        daily_vol = 0.03  # 3% daily volatility
        candle_vol = daily_vol * np.sqrt(minutes / (24 * 60))
        returns = np.random.normal(0.0001, candle_vol, num_candles)

        # Add some trend and mean reversion
        trend = np.sin(np.linspace(0, 4 * np.pi, num_candles)) * 0.0001
        returns = returns + trend

        # Calculate prices
        prices = start_price * np.exp(np.cumsum(returns))

        # Generate OHLCV
        candles = []
        start_time = datetime.now() - timedelta(days=days)

        for i in range(num_candles):
            close = prices[i]
            volatility = close * candle_vol

            high = close + abs(np.random.normal(0, volatility))
            low = close - abs(np.random.normal(0, volatility))
            open_price = low + np.random.random() * (high - low)

            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            volume = np.random.exponential(100) * close / 10000

            candles.append({
                "timestamp": start_time + timedelta(minutes=i * minutes),
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": round(volume, 4),
            })

        return pd.DataFrame(candles)
