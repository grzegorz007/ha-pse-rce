# PSE RCE Price Chain for Home Assistant

A custom Home Assistant integration that fetches dynamic Polish Market Energy Prices (Rynkowe Ceny Energii – RCE) directly from the official Polskie Sieci Elektroenergetyczne (PSE) API. It formats, aggregates, and transforms price arrays specifically tailored for **EMHASS** linear optimization payloads and home energy management systems.

---

## Features

* **EMHASS Native Alignment**: Automatically resamples and averages native 15-minute intervals into clean 30-minute time slots required by EMHASS solvers.
* **Flexible Starting Reference**: Start forecasts directly from the next active time slot or aligned from midnight.
* **Smart Rollover Fallback**: Bridges publication gaps when next-day tariffs are unpublished by automatically repeating full 24-hour cyclical profiles, preventing LP solver interruptions.
* **Price Modifications**:
  * **Configurable Multipliers**: Apply taxation or custom coefficients (e.g., VAT at `1.23`).
  * **Fixed Fee Offsets**: Add grid and distribution charges directly in `PLN/kWh`.
  * **Negative Price Clamping**: Optional toggle to floor sub-zero energy prices to `0.00 PLN/kWh`.
* **Analytical Sensor Suite**:
  * `sensor.pse_rce_price_chain`: Current price state alongside the complete price sequence inside attributes (`list`).
  * `sensor.pse_rce_today_min_price`: Calendar-day minimum price with exact timestamp (`dtime`).
  * `sensor.pse_rce_today_max_price`: Calendar-day peak price with exact timestamp (`dtime`).
* **Complete UI Configuration**: Full configuration and options flow support without touching `configuration.yaml`.
* **Full Localization**: Native English (`en`) and Polish (`pl`) translation support.

---

## Installation

### HACS (Custom Repository)
1. Open **HACS** in your Home Assistant instance.
2. Navigate to **Integrations** > click the three dots in the top right > select **Custom repositories**.
3. Paste the URL of this repository, select **Integration** as the category, and click **Add**.
4. Search for **PSE RCE Price Chain** and click **Download**.
5. Restart Home Assistant.

### Manual Installation
1. Download the `custom_components/pse_rce` folder from the latest release.
2. Copy the entire directory into your Home Assistant `<config_dir>/custom_components/` path.
3. Restart Home Assistant.

---

## Configuration

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **PSE RCE Price Chain**.
3. Set your operational parameters:
   * **Forecast Horizon**: Total horizon window in hours (e.g., `48` for a 48-hour outlook).
   * **Start from Midnight**: Check to align the forecast array to 00:00:00.
   * **Time Resolution**: Choose between native `15m` or EMHASS-compatible `30m`.
   * **Data Fallback Strategy**: Choose how to handle missing future hours (`Repeat 24h cycle`, `Last known value`, or `Zeros`).
   * **Price Multiplier**: Multiplier applied to raw energy rates (default: `1.23`).
   * **Fixed Price Offset**: Additional distribution/network surcharge added per kWh.
   * **Clamp Negative Prices**: Set whether negative prices should resolve to zero.

---

## EMHASS Integration Example

Use the forecast array directly within your EMHASS REST command payload:

```yaml
rest_command:
  emhass_dayahead_optim:
    url: http://localhost:5000/action/dayahead-optim
    method: POST
    content_type: "application/json"
    payload: >-
      {
        "load_cost_forecast": {{ state_attr('sensor.pse_rce_price_chain', 'list') }},
        "prod_price_forecast": {{ state_attr('sensor.pse_rce_price_chain', 'list') }}
      }
