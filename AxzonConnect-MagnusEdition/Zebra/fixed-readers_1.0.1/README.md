# AxzonConnect for Zebra IoT Connector

This software is intended for the Zebra IoT Connector and is supported by the following fixed readers:
- **FX9600**
- **FX7500**
- **ATR7000**

The readers must have firmware version **3.28.18** or newer.

## Zebra IoT Connector Information
For more details, visit the [Zebra IoT Connector documentation](https://zebradevs.github.io/rfid-ziotc-docs/index.html).

The AxzonConnect distribution package was built using the process described [here](https://zebradevs.github.io/rfid-ziotc-docs/user_apps/packaging_and_deployment.html).

**Note:** The current version of AxzonConnect supports only **Antenna Port 1**.

---

## Execution Steps

1. **Configure the IoT Connector Tag Data Interface:**
   Set up the desired endpoint (e.g., MQTT, TCP, AWS IoT Core, etc.).
2. **Configure the Management and Control Interfaces:**
   Use the default connection: `LOCAL-REST`.
3. **Set the Management Events Interface:**
   Set it to `NONE`.
   ![Management Events Interface](https://axzon-docs-public.s3.us-east-2.amazonaws.com/images/Zebra+AxzonConnect/readme-1.png)
4. **Install the AxzonConnect Application:**
   Use the distribution package `axzon-connect_1.0.1.deb`. Install it through the reader's web interface under the **Applications** menu:
   ![Install Application](https://axzon-docs-public.s3.us-east-2.amazonaws.com/images/Zebra+AxzonConnect/readme-2-magnus-version.png)
5. **Start and stop the program as desired**

---

## Features of AxzonConnect

AxzonConnect Magnus Edition continuously looks for Magnus® S3 tags and reports the temperature measurement, among other parameters, every ten seconds. This version only supports Temperature Measurements, not Sensor Code measurements. The next version of AxzonConnect Magnus Edition will support Sensor Code measurements.

---
