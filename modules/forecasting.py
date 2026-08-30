"""
Time series forecasting for user weight trend using Prophet.
"""

import pandas as pd
from prophet import Prophet



def prepare_prophet_input(user_id):
    from modules.analytics import get_weight_history
    """Pulls weight history and reshapes it into Prophet's required
    ds/y column format. Raises if there's not enough data to forecast
    meaningfully - Prophet technically runs on very little data, but
    the result is unreliable below ~2 weeks."""
    df = get_weight_history(user_id)

    if len(df) < 14:
        raise ValueError(
            f"Only {len(df)} days of weight history found. "
            f"Need at least 14 days for a meaningful forecast."
        )

    prophet_df = df.rename(columns={"log_date": "ds", "weight_kg": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    return prophet_df


def fit_and_forecast(user_id, periods_days=28):
    """Fits Prophet on the user's weight history and forecasts forward.
    Returns (model, forecast_df) - forecast_df includes both the historical
    fitted values AND the future predictions, with yhat_lower/yhat_upper
    as the confidence interval bounds."""
    prophet_df = prepare_prophet_input(user_id)

    model = Prophet(
        daily_seasonality=False,   # a single daily weigh-in has no intra-day pattern to model
        weekly_seasonality=True,   # weekends often differ from weekdays (diet/activity)
        yearly_seasonality=False   # not enough history yet to trust a yearly pattern
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods_days)
    forecast = model.predict(future)

    return model, forecast


def generate_forecast_chart(model, forecast, save_path=None):
    """Returns a matplotlib figure showing history + forecast + confidence band.
    If save_path is given, also saves it as a PNG (useful for the PDF report
    in Phase 6)."""
    fig = model.plot(forecast)
    ax = fig.gca()
    ax.set_xlabel("Date")
    ax.set_ylabel("Weight (kg)")
    ax.set_title("Weight Forecast")

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")

    return fig


def get_forecast_summary(forecast, target_weight=None):
    """Turns the raw forecast into a human-readable sentence.
    If target_weight is given, estimates roughly when that weight might be
    reached - a simple nearest-match lookup, not a precise inverse model."""
    last_row = forecast.iloc[-1]
    predicted_date = last_row["ds"].strftime("%B %d, %Y")
    predicted_weight = round(last_row["yhat"], 1)
    lower = round(last_row["yhat_lower"], 1)
    upper = round(last_row["yhat_upper"], 1)

    summary = (
        f"At your current trend, your projected weight around {predicted_date} "
        f"is approximately {predicted_weight} kg (range: {lower}–{upper} kg)."
    )

    if target_weight is not None:
        # Only look at the FUTURE portion of the forecast for this estimate
        future_only = forecast[forecast["ds"] > pd.Timestamp.now()]
        closest_match = (future_only["yhat"] - target_weight).abs().idxmin()
        eta_row = future_only.loc[closest_match]
        eta_date = eta_row["ds"].strftime("%B %d, %Y")
        summary += (
            f" Based on this trend, you may reach {target_weight} kg around "
            f"{eta_date} - treat this as a rough estimate, not a guarantee."
        )

    return summary