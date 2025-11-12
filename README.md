<h1 align="center">🤖 Network Automation 1️⃣0️⃣1️⃣<br /><br />
<div align="center">
<img src="logo.png" width="500"/>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Cisco-1BA0D7?style=flat&logo=cisco&labelColor=555555&logoColor=white" alt="Cisco"/>
  <img src="https://img.shields.io/badge/Python-gray?style=flat&logo=python" alt="Python"/>
  <a href="https://www.linkedin.com/in/asandovalros"><img src="https://img.shields.io/badge/Howdy!-LinkedIn-blue?style=flat"/></a>
</div></h1>

Learn how to automate network devices like a pro — from CLI scripting to model-based automation!  
This repository introduces **hands-on network automation with Python**, guiding you through three essential approaches: **Netmiko (CLI-based)**, **pyATS (CLI-based, but much more robust)**, and **Ncclient (NETCONF-based)**.

---

## 📘 Notebooks Included

### 1️⃣ `talking_netmiko_with_my_network.ipynb`  
**🚀 CLI interaction with Python Netmiko**

Your first step into network automation!  
This notebook walks you through connecting to a **Cisco IOS-XR router**, reading configurations, making safe changes, and discovering how automation makes manual CLI obsolete.

**🧰 Prerequisites**
- 🐍 Python 3.9+  
- 🔌 SSH access to your Cisco IOS-XR device  
  → Use the [Always-On Cisco IOSXR DevNet Sandbox](https://devnetsandbox.cisco.com/DevNet/catalog/ios-xr-always-on_ios-xr-always-on#instructions)  
- 👤 `.env` file with credentials and device URL (included in this repo)

---

### 2️⃣ `talking_ncclient_with_my_network.ipynb`  
**🚀 NETCONF interaction with Python Ncclient**

Step into **model-driven network automation**!  
This notebook demonstrates how to use **Ncclient** to send automated NETCONF payloads to a Cisco IOS-XR router — letting you configure and retrieve data in a structured, standardized way.

**🧰 Prerequisites**
- 🐍 Python 3.9+  
- 🔌 SSH access to your Cisco IOS-XR device  
  → Use the [Always-On Cisco IOSXR DevNet Sandbox](https://devnetsandbox.cisco.com/DevNet/catalog/ios-xr-always-on_ios-xr-always-on#instructions)  
- 👤 `.env` file with credentials and device URL (included in this repo)

---

### 2️⃣ `talking_pyats_with_my_network.ipynb`  
**🚀 CLI interaction with pyATS**

**Cleaver network automation** with a Cisco-developed, open code framework!  
This notebook demonstrates how to use **pyATS** to orchestrate your topology using learning capabilities, snapshots and more.

**🧰 Prerequisites**
- 🐍 Python 3.9+  
- 🔌 SSH access to your Cisco IOS-XR device  
  → Use the [Always-On Cisco IOSXR DevNet Sandbox](https://devnetsandbox.cisco.com/DevNet/catalog/ios-xr-always-on_ios-xr-always-on#instructions)  
- 👤 `pyATS/topology.yaml` file with credentials and device URL (included in this repo)

---

## ⚙️ Setup

1. Clone this repository  
   ```bash
   git clone https://github.com/yourusername/network-automation-foundations.git
   cd network-automation-foundations
   ```

2. Create a virtual environment & install dependencies  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Add your `.env` file (use the sample provided)  
   ```bash
    XR_HOST=sandbox-iosxr-1.cisco.com
    XR_USER=admin
    XR_PASS=C1sco12345
   ```

4. Add your `pyATS/topology.yaml` file (use the sample provided)

   ```yaml
   testbed:
    name: NetworkAutoDemo
    devices:
      sandbox1:
        os: iosxr
        type: router
        platform: ASR9K
        connections:
          cli:
            protocol: ssh
            ip: sandbox-iosxr-1.cisco.com
            port: 22
            arguments:
              connection_timeout: 60
              connection_retries: 3
        credentials:
          default:
            username: admin
            password: C1sco12345
   ```

5. Open the notebooks in Jupyter.

---

## 🎯 What You’ll Learn

- 🔧 How to automate Cisco IOS-XR devices  
- 🧠 The difference between CLI-based and model-based automation  
- 💡 Why network engineers should script their workflows  
- ⚡ Real-world use of Netmiko and Ncclient libraries  

---

## 🛠️ Tech Stack

- Python 3.9+  
- Jupyter Notebooks  
- [Netmiko](https://github.com/ktbyers/netmiko)  
- [Ncclient](https://github.com/ncclient/ncclient)  
- [pyATS](https://developer.cisco.com/docs/pyats/)
- Cisco DevNet Sandbox

---

## ⚖️ Automation vs Manual CLI — Why It Matters

| Feature / Approach                     | Manual CLI Management 🧍‍♂️ | CLI Automation (Netmiko) ⚙️ | NETCONF Automation (Ncclient) 🤖 |
|----------------------------------------|----------------------------|------------------------------|----------------------------------|
| **Configuration Speed**                | Slow, device-by-device     | Fast, script executes across multiple devices | Extremely fast with structured operations |
| **Error Handling**                     | Human-prone (typos, missed commands) | Basic error checking via scripts | Built-in transaction validation |
| **Consistency Across Devices**         | Hard to maintain manually  | Repeatable with same script | Guaranteed via data models (YANG) |
| **Scalability**                        | Limited by human capacity  | Scales with script automation | Scales with orchestration tools |
| **Visibility & Data Extraction**       | Manual show commands       | Automated parsing of outputs | Structured data retrieval via XML |
| **Change Rollback**                    | Manual recovery            | Scripted if built-in         | Native commit/rollback support |
| **Standardization**                    | Vendor-specific syntax     | Still CLI-based, vendor-specific | Model-driven, vendor-neutral |
| **Best For**                           | Small labs, quick fixes    | Transitional automation phase | Large-scale, modern automation |

> In short: **Netmiko** helps you automate what you already do manually.  
> **Ncclient** helps you evolve to truly programmable, model-driven networking.

---

<div align="center"><br />
    Made with ☕️ by Poncho Sandoval - <code>Developer Advocate 🥑 @ DevNet - Cisco Systems 🇵🇹</code><br /><br />
    <a href="mailto:alfsando@cisco.com?subject=Question%20about%20[NetworkAutomation101]&body=Hello,%0A%0AI%20have%20a%20question%20regarding%20your%20project.%0A%0AThanks!">
        <img src="https://img.shields.io/badge/Contact%20me!-blue?style=flat&logo=gmail&labelColor=555555&logoColor=white" alt="Contact Me via Email!"/>
    </a>
    <a href="https://github.com/ponchotitlan/network_automation_journey_101/issues/new">
      <img src="https://img.shields.io/badge/Open%20Issue-2088FF?style=flat&logo=github&labelColor=555555&logoColor=white" alt="Open an Issue"/>
    </a>
    <a href="https://github.com/ponchotitlan/network_automation_journey_101/fork">
      <img src="https://img.shields.io/badge/Fork%20Repository-000000?style=flat&logo=github&labelColor=555555&logoColor=white" alt="Fork Repository"/>
    </a>
</div>