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
   ![Install Application](https://axzon-docs-public.s3.us-east-2.amazonaws.com/images/Zebra+AxzonConnect/readme-2.png)
5. **Start and Stop the Program as Needed:**
   - **Warning:** Keep tags not intended for immediate logging away from the reader's antenna. The program will automatically start the logging process for all new tags.

---

## Features of AxzonConnect

The AxzonConnect program performs the following tasks:

- When it finds new tags in **Sleep mode**, it writes to every tag the logging configuration specified in the local file `OpusConfig.json` located in the `/apps` directory and then arms the tags. The logging process starts for all new tags. It reports the status of each tag following the format of the `OpusStatus.json` file.

- When it finds tags that are **logging** or **finished logging**, it reports the tag status and the logged data following the format of the `OpusStatus.json` file. There could be multiple reports for each tag.

- For tags that remain **15 or more seconds** in the field of view of the reader, the program reports the tag status every 15 seconds.

---

### Configuration
The `OpusConfig.json` file located in the `/apps` directory of the reader can be updated with any valid configuration as desired.  
**Important:** Restart the AxzonConnect program after updating the configuration file to apply changes.

---
