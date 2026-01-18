"""
Data Loader for RL Training

Loads historical OHLCV data and computes technical indicators.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from sklearn.preprocessing import StandardScaler


class DataLoader:
    """
    Loads and preprocesses historical OHLCV data for RL training.
    """

    def __init__(self, data_dir: str = "./data/historical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = StandardScaler()
        self._raw_data: Optional[pd.DataFrame] = None
        self._processed_data: Optional[pd.DataFrame] = None

    def load_data(self, filename: str = "btcusd_5m.parquet") -> pd.DataFrame:
        """Load historical data from parquet file."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Data file not found: {filepath}. "
                "Run 'python manage.py fetch_historical_data' first."
            )

        if filename.endswith(".parquet"):
            self._raw_data = pd.read_parquet(filepath)
        elif filename.endswith(".csv"):
            self._raw_data = pd.read_csv(filepath, parse_dates=["timestamp"])
        else:
            raise ValueError(f"Unsupported file format: {filename}")

        self._raw_data = self._raw_data.sort_values("timestamp").reset_index(drop=True)
        return self._raw_data

    def compute_indicators(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Compute technical indicators for the dataset."""
        if df is None:
            df = self._raw_data

        if df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        df = df.copy()

        # RSI
        rsi = RSIIndicator(close=df["close"], window=14)
        df["rsi_14"] = rsi.rsi()

        # MACD
        macd = MACD(close=df["close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_diff"] = macd.macd_diff()

        # Bollinger Bands
        bb = BollingerBands(close=df["close"], window=20, window_dev=2)
        df["bb_high"] = bb.bollinger_hband()
        df["bb_low"] = bb.bollinger_lband()
        df["bb_mid"] = bb.bollinger_mavg()
        # Position within bands (-1 to 1)
        df["bb_position"] = (df["close"] - df["bb_mid"]) / (
            (df["bb_high"] - df["bb_low"]) / 2 + 1e-8
        )

        # ATR (volatility)
        atr = AverageTrueRange(
            high=df["high"], low=df["low"], close=df["close"], window=14
        )
        df["atr"] = atr.average_true_range()
        df["atr_normalized"] = df["atr"] / df["close"]  # Percentage of price

        # ADX (trend strength)
        adx = ADXIndicator(
            high=df["high"], low=df["low"], close=df["close"], window=14
        )
        df["adx"] = adx.adx()

        # Volume indicators
        df["volume_sma_20"] = SMAIndicator(close=df["volume"], window=20).sma_indicator()
        df["volume_ratio"] = df["volume"] / (df["volume_sma_20"] + 1e-8)

        # Price momentum
        df["momentum_1h"] = df["close"].pct_change(periods=12)  # 12 * 5min = 1h
        df["momentum_4h"] = df["close"].pct_change(periods=48)  # 48 * 5min = 4h
        df["momentum_24h"] = df["close"].pct_change(periods=288)  # 288 * 5min = 24h

        # Price returns
        df["returns"] = df["close"].pct_change()
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))

        # Stochastic
        stoch = StochasticOscillator(
            high=df["high"], low=df["low"], close=df["close"]
        )
        df["stoch_k"] = stoch.stoch()
        df["stoch_d"] = stoch.stoch_signal()

        # Drop NaN rows from indicator calculations
        df = df.dropna().reset_index(drop=True)

        self._processed_data = df
        return df

    def get_feature_columns(self) -> list:
        """Get list of feature columns for state encoding."""
        return [
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_diff",
            "bb_position",
            "atr_normalized",
            "adx",
            "volume_ratio",
            "momentum_1h",
            "momentum_4h",
            "momentum_24h",
            "returns",
            "stoch_k",
            "stoch_d",
        ]

    def normalize_features(
        self, df: Optional[pd.DataFrame] = None, fit: bool = True
    ) -> pd.DataFrame:
        """Normalize features using StandardScaler."""
        if df is None:
            df = self._processed_data

        if df is None:
            raise ValueError("No processed data. Call compute_indicators() first.")

        feature_cols = self.get_feature_columns()
        df = df.copy()

        if fit:
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            df[feature_cols] = self.scaler.transform(df[feature_cols])

        return df

    def split_data(
        self, df: Optional[pd.DataFrame] = None, train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data chronologically into train and test sets."""
        if df is None:
            df = self._processed_data

        if df is None:
            raise ValueError("No processed data. Call compute_indicators() first.")

        split_idx = int(len(df) * train_ratio)
        train_df = df.iloc[:split_idx].reset_index(drop=True)
        test_df = df.iloc[split_idx:].reset_index(drop=True)

        return train_df, test_df

    def prepare_training_data(
        self, filename: str = "btcusd_5m.parquet", train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Full pipeline: load, compute indicators, normalize, split.

        Returns:
            Tuple of (train_df, test_df)
        """
        self.load_data(filename)
        self.compute_indicators()

        # Split first, then normalize (fit on train only)
        train_df, test_df = self.split_data(train_ratio=train_ratio)

        # Fit scaler on training data only
        feature_cols = self.get_feature_columns()
        self.scaler.fit(train_df[feature_cols])

        # Transform both sets
        train_df = train_df.copy()
        test_df = test_df.copy()
        train_df[feature_cols] = self.scaler.transform(train_df[feature_cols])
        test_df[feature_cols] = self.scaler.transform(test_df[feature_cols])

        return train_df, test_df

    def get_ohlcv_at_index(self, df: pd.DataFrame, idx: int) -> dict:
        """Get OHLCV data at specific index."""
        row = df.iloc[idx]
        return {
            "timestamp": row["timestamp"],
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
        }

    def simulate_trade_outcome(
        self,
        df: pd.DataFrame,
        entry_idx: int,
        direction: str,  # "long" or "short"
        leverage: float = 1.0,
        hold_periods: int = 12,  # 1 hour for 5min data
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10,
    ) -> dict:
        """
        Simulate trade outcome for reward calculation.

        Args:
            df: DataFrame with OHLCV data
            entry_idx: Index where trade is entered
            direction: "long" or "short"
            leverage: Trading leverage
            hold_periods: Number of periods to hold (max)
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage

        Returns:
            dict with trade outcome metrics
        """
        if entry_idx + hold_periods >= len(df):
            hold_periods = len(df) - entry_idx - 1

        entry_price = df.iloc[entry_idx]["close"]
        max_idx = entry_idx + hold_periods

        # Track price path
        prices = df.iloc[entry_idx : max_idx + 1]["close"].values
        highs = df.iloc[entry_idx : max_idx + 1]["high"].values
        lows = df.iloc[entry_idx : max_idx + 1]["low"].values

        # Calculate PnL at each step
        if direction == "long":
            returns = (prices - entry_price) / entry_price * leverage
            max_drawdown = (entry_price - lows.min()) / entry_price * leverage
            was_stopped = lows.min() <= entry_price * (1 - stop_loss_pct / leverage)
            hit_tp = highs.max() >= entry_price * (1 + take_profit_pct / leverage)
        else:  # short
            returns = (entry_price - prices) / entry_price * leverage
            max_drawdown = (highs.max() - entry_price) / entry_price * leverage
            was_stopped = highs.max() >= entry_price * (1 + stop_loss_pct / leverage)
            hit_tp = lows.min() <= entry_price * (1 - take_profit_pct / leverage)

        # Final PnL
        exit_price = prices[-1]
        if direction == "long":
            pnl = (exit_price - entry_price) / entry_price * leverage
        else:
            pnl = (entry_price - exit_price) / entry_price * leverage

        # Check for liquidation (simplified: 80% loss)
        liquidation_threshold = 0.8 / leverage
        was_liquidated = max_drawdown >= liquidation_threshold

        return {
            "pnl": pnl,
            "max_drawdown": max_drawdown,
            "was_stopped": was_stopped,
            "hit_take_profit": hit_tp,
            "was_liquidated": was_liquidated,
            "hold_periods": hold_periods,
            "entry_price": entry_price,
            "exit_price": exit_price,
        }
