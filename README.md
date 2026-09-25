# **CS5002 Senior Design: DigiDarts**

## **Table of Contents**
  - [1. Project Description](README.md)
  - [2. Design Specifications](README.md)


## **1. Project Description**

### **Meet the Team**
  - [Evan Heidenreich](team/Evan-Heidenreich-Biography.md)
  - [Nicholas Rigg](team/Nicholas-Rigg-Biography.md)
  - [Jacob Curtis](team/Jacob-Curtis-Biography.md) 

### **Advisor**
  - Dr. William Hawkins III - Asst Professor - Educator F2


### **Project Topic Overview**

Our goal is to develop an automated dartboard that utilizes computer vision to track darts thrown and relays the information back to the user via an app/website where users can play numerous dart-board games such as 501, 301, Cricket, & around the world. We will utilize cameras to track darts thrown and develop simulations to get the greatest accuracy. The website will also keep track of players' stats like games one/lost, win percentage, etc. 

## **2. Design Specifications**

#### **Back-End Specifications**

  - **Language/Framework:** Python with Flask, serving the API that connects the computer vision pipeline to the front-end
  - **Computer Vision:** OpenCV paired with a custom-trained ML model for detecting dart tip location and scoring zone
  - **Database:** Supabase, used to store player accounts, game history, and stats (games won/lost, win percentage, etc.)
  - **API/Communication Layer:** Not yet finalized — under evaluation between a REST API and a REST + WebSockets approach for delivering live scoring updates

#### **Front-End Specifications**

  - **Platform/Framework:** Not yet finalized — planned as an app/website, exact framework to be determined
  - **Key Features:**
    - Game mode selection (501, 301, Cricket, Around the World)
    - Live scoring display synced with dart throws detected by the back-end
    - Player stats and leaderboards (games won/lost, win percentage, etc.)

#### **Hardware Specifications**

  - Dell mini form-factor 7060 Computers
  - Dartboard (Viper)
  - x2 Arducam 2.3MP AR0234 Color Global Shutter USB 3.0 Camera Module SKU: B0495C
  - LED Light Strips
  - Manufactur 3D printed Camera and light ring

