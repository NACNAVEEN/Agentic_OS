# BACnet Protocol Guide

## What is BACnet?

BACnet (Building Automation and Control Networks) is a data communication protocol for building automation and control systems (BACS). It was developed under the auspices of ASHRAE (American Society of Heating, Refrigerating and Air-Conditioning Engineers) and is an ISO global standard (ISO 16484-5).

## Key Concepts

### Object Types
BACnet defines a set of standard object types that represent the components and functions of building automation systems:

- **Analog Input (AI)**: Represents a sensor reading (e.g., temperature, humidity, pressure)
- **Analog Output (AO)**: Represents a control output (e.g., valve position, damper position)
- **Analog Value (AV)**: Represents a calculated or stored value
- **Binary Input (BI)**: Represents a two-state sensor (e.g., switch, status)
- **Binary Output (BO)**: Represents a two-state control output (e.g., relay, start/stop)
- **Binary Value (BV)**: Represents a two-state calculated or stored value

### BACnet Services
- **Who-Is / I-Am**: Device discovery
- **Read Property**: Read data from a BACnet device
- **Write Property**: Write data to a BACnet device
- **Subscribe COV**: Subscribe to Change of Value notifications
- **Alarm and Event**: Alarm management

### Network Architecture
BACnet supports multiple network types:
1. **BACnet/IP**: Uses standard IP networking (most common)
2. **BACnet MS/TP**: Uses RS-485 serial communication
3. **BACnet Ethernet**: Direct Ethernet framing

## Common Applications in Building Management

### HVAC Control
- Air Handling Unit control and monitoring
- Chiller plant optimization
- Variable Air Volume (VAV) control
- Boiler sequencing

### Energy Management
- Demand limiting
- Load shedding
- Time-of-use scheduling
- Trending and data logging

### Alarm Management
- Priority-based alarm handling
- Alarm routing and notification
- Alarm acknowledgment workflows

## Integration with Modern Systems
BACnet can be integrated with modern IoT platforms through:
- BACnet gateways
- BACnet API servers
- Cloud-based BACnet services
- MQTT bridges
