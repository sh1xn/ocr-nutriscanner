import re
import time
import os
import json
import base64
import requests
import cv2
import numpy as np
import pytesseract
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NutriScan | Live Nutrition Scanner</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {
    color-scheme: dark;
    --bg: #080d14;
    --surface: rgba(18, 28, 42, .72);
    --surface-strong: rgba(20, 32, 47, .92);
    --line: rgba(177, 211, 226, .14);
    --text: #edf7fb;
    --muted: #9cb0bf;
    --mint: #65f0c1;
    --cyan: #70d9f5;
    --shadow: 0 24px 70px rgba(0, 0, 0, .28);
}
* { box-sizing: border-box; }
html { min-height: 100%; background: var(--bg); }
body {
    min-height: 100vh; margin: 0; font-family: 'DM Sans', sans-serif;
    color: var(--text);
    background:
      radial-gradient(ellipse at 12% 8%, rgba(34, 211, 170, .14), transparent 34%),
      radial-gradient(ellipse at 90% 18%, rgba(74, 133, 255, .15), transparent 32%),
      radial-gradient(ellipse at 70% 90%, rgba(102, 82, 255, .09), transparent 35%),
      var(--bg);
    background-attachment: fixed;
}
header {
    position: relative; overflow: hidden; padding: 28px max(5%, calc((100% - 1400px) / 2));
    border-bottom: 1px solid var(--line);
    background: rgba(8, 15, 24, .66); backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px);
}
header:after { content: ''; position: absolute; width: 340px; height: 200px; right: 8%; top: -145px; background: var(--mint); filter: blur(100px); opacity: .15; pointer-events: none; }
header h1 { margin: 0; font: 700 clamp(27px, 3vw, 38px)/1.2 'Space Grotesk', sans-serif; letter-spacing: -.04em; }
header p { margin: 9px 0 0; color: #b4c8d5; font-size: 15px; }
main { max-width: 1440px; margin: 28px auto; padding: 0 26px 42px; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: 22px; align-items: start; }
#scannerSection { width: 100%; }
#cameraVideo { max-height: min(68vh, 760px); min-height: 320px; object-fit: contain; }
#dashboardSection { width: 100%; scroll-margin-top: 28px; }
#dashboardSection .metrics { grid-template-columns: repeat(4, minmax(0, 1fr)); }
#recognizedSection { width: 100%; }
#loadingBar {
    position: fixed; z-index: 2000; inset: 0 0 auto; height: 4px;
    opacity: 0; pointer-events: none; transition: opacity .22s ease;
    background: rgba(255,255,255,.08);
}
#loadingBar.active { opacity: 1; }
#loadingBar .progress {
    width: 35%; height: 100%; border-radius: 0 8px 8px 0;
    background: linear-gradient(90deg, #65f0c1, #70d9f5, #65f0c1);
    box-shadow: 0 0 18px rgba(101,240,193,.7);
    animation: loadingSweep 1.15s ease-in-out infinite;
}
@keyframes loadingSweep {
    0% { transform: translateX(-110%); }
    100% { transform: translateX(390%); }
}
body.is-loading { cursor: progress; }
body.is-loading button { pointer-events: none; opacity: .7; }
.scan-status {
    display: none; position: sticky; top: 8px; z-index: 100;
    margin: 0 0 16px; padding: 12px 16px; border-radius: 13px;
    color: #dffdf4; border: 1px solid rgba(101,240,193,.24);
    background: rgba(12, 30, 34, .88); backdrop-filter: blur(16px);
}
.scan-status.visible { display: block; }
.card {
    min-width: 0; padding: clamp(20px, 2.2vw, 30px); border-radius: 24px;
    background: linear-gradient(135deg, rgba(255,255,255,.055), rgba(255,255,255,.025)), var(--surface);
    border: 1px solid var(--line); box-shadow: var(--shadow);
    backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
}
h2 { margin: 0 0 20px; font: 600 clamp(20px, 2vw, 25px)/1.25 'Space Grotesk', sans-serif; letter-spacing: -.025em; }
#cameraVideo {
    display: block; width: 100%; min-height: 260px; max-height: 520px; object-fit: contain;
    border-radius: 17px; background: #05080d; border: 1px solid rgba(255,255,255,.1);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,.025);
}
button {
    border: 1px solid rgba(101, 240, 193, .25); border-radius: 12px; padding: 12px 16px;
    background: linear-gradient(135deg, #65f0c1, #44cfae); color: #062219;
    font: 700 14px 'DM Sans', sans-serif; cursor: pointer; margin: 10px 7px 0 0;
    box-shadow: 0 8px 24px rgba(55, 213, 168, .12); transition: transform .18s ease, filter .18s ease, box-shadow .18s ease;
}
button:hover { transform: translateY(-2px); filter: brightness(1.06); box-shadow: 0 12px 28px rgba(55, 213, 168, .2); }
button:active { transform: translateY(0); }
button.secondary { color: #d9e8f0; background: rgba(147, 174, 197, .09); border-color: var(--line); box-shadow: none; }
button.secondary:hover { background: rgba(147, 174, 197, .16); }
button:disabled { opacity: .45; cursor: not-allowed; transform: none; }
.status { color: var(--muted); font-size: 14px; line-height: 1.65; }
#status { padding: 11px 13px; border-radius: 12px; background: rgba(112, 217, 245, .055); border: 1px solid rgba(112, 217, 245, .12); }
.metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; margin-top: 20px; }
.metric {
    min-width: 0; padding: 18px; border-radius: 17px;
    background: linear-gradient(145deg, rgba(123, 231, 205, .085), rgba(255,255,255,.025));
    border: 1px solid rgba(145, 220, 207, .13); box-shadow: inset 0 1px 0 rgba(255,255,255,.035);
    transition: transform .18s ease, border-color .18s ease, background .18s ease;
}
.metric:hover { transform: translateY(-2px); border-color: rgba(101, 240, 193, .32); background: rgba(101, 240, 193, .09); }
.metric span { display: block; color: #f4f8fb; font: 700 clamp(16px, 1.45vw, 20px)/1.25 'Space Grotesk', sans-serif; letter-spacing: -.015em; text-transform: none; overflow-wrap: anywhere; }
.metric strong { display: block; margin-top: 8px; color: #b9c9d4; font: 500 clamp(14px, 1.2vw, 17px)/1.45 'DM Sans', sans-serif; overflow-wrap: anywhere; }
.metric.category-card { grid-column: 1 / -1; padding: 22px 24px; border-color: rgba(255, 160, 70, .38); background: linear-gradient(120deg, rgba(255, 143, 51, .17), rgba(255,255,255,.035)); }
.metric.category-card span { color: #ffb56b; font-size: 13px; text-transform: uppercase; letter-spacing: .1em; }
.metric.category-card strong { margin-top: 5px; color: #fff4e8; font: 700 clamp(22px, 2.4vw, 30px)/1.2 'Space Grotesk', sans-serif; }
.metric.category-card small { display: block; margin-top: 8px; color: #d4c3b4; font-size: 13px; line-height: 1.55; }
.empty-state { grid-column: 1 / -1; padding: 26px; border: 1px dashed rgba(156, 188, 207, .22); background: rgba(255,255,255,.025); border-radius: 16px; color: var(--muted); line-height: 1.7; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; padding: 18px; border-radius: 15px; color: #cce4ed; background: rgba(2, 8, 14, .48); border: 1px solid var(--line); font: 13px/1.7 ui-monospace, SFMono-Regular, Consolas, monospace; max-height: 360px; overflow: auto; }
.modal { display: none; position: fixed; inset: 0; z-index: 1000; padding: 20px; overflow: auto; background: rgba(1, 5, 10, .78); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); }
.modal.open { display: flex; align-items: center; justify-content: center; }
.modal-panel { width: min(100%, 1050px); max-height: 94vh; overflow: auto; padding: 24px; color: var(--text); border: 1px solid rgba(177,211,226,.18); border-radius: 22px; background: rgba(15, 25, 38, .96); box-shadow: 0 30px 100px rgba(0,0,0,.55); }
.canvas-wrap { width: 100%; max-height: 65vh; overflow: auto; background: #03070b; border: 1px solid var(--line); border-radius: 14px; text-align: center; }
#cropCanvas { display: block; max-width: 100%; height: auto; margin: auto; cursor: crosshair; touch-action: none; }
.modal-actions { display: flex; flex-wrap: wrap; gap: 8px; }
::selection { background: rgba(101,240,193,.28); color: white; }
@media (max-width: 1100px) { #dashboardSection .metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 900px) { #cameraVideo { max-height: 56vh; min-height: 250px; } #dashboardSection .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) {
    header { padding: 22px 20px; }
    main { margin: 18px auto; padding: 0 12px 26px; }
    .layout { gap: 14px; }
    .card { padding: 17px; border-radius: 19px; }
    .metrics { gap: 9px; }
    .metric { padding: 13px; border-radius: 14px; }
    .metric strong { font-size: 15px; }
    .metric span { font-size: 16px; }
    #cameraVideo { min-height: 190px; }
    #dashboardSection .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    button { padding: 11px 12px; font-size: 13px; }
    .modal { padding: 8px; }
    .modal-panel { padding: 14px; border-radius: 17px; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; scroll-behavior: auto !important; } }

/* NutriScan x Swiggy-inspired light UI refresh */
:root {
    color-scheme: light;
    --bg: #ffffff;
    --surface: #ffffff;
    --surface-strong: #ffffff;
    --line: #ececec;
    --text: #202127;
    --muted: #686b73;
    --mint: #ff5200;
    --cyan: #ff8a50;
    --shadow: 0 5px 22px rgba(25, 25, 25, .075);
}
html { background: #fff; scroll-behavior: smooth; }
body {
    color: #202127;
    background: #fff;
    background-attachment: initial;
    font-family: 'DM Sans', sans-serif;
}
header {
    overflow: visible;
    padding: 20px max(5%, calc((100% - 1280px) / 2));
    color: #202127;
    background: #fff;
    border-bottom: 1px solid #f0f0f0;
    box-shadow: 0 4px 18px rgba(0,0,0,.035);
    backdrop-filter: none;
}
header:after { display: none; }
header h1 {
    display: flex; align-items: center; gap: 12px;
    color: #202127; font: 700 clamp(27px, 3vw, 34px)/1.2 'Space Grotesk', sans-serif;
    letter-spacing: -.045em;
}
header h1::first-letter { color: #ff5200; }
header p { margin: 5px 0 0 48px; color: #777982; font-size: 14px; }
main { max-width: 1280px; margin: 30px auto; padding: 0 30px 54px; }
.layout { grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: 24px; }
.card {
    padding: clamp(20px, 2.2vw, 28px);
    border: 1px solid #ededed; border-radius: 22px;
    background: #fff; box-shadow: 0 5px 24px rgba(20,20,20,.055);
    backdrop-filter: none; -webkit-backdrop-filter: none;
}
h2 { color: #202127; font-size: clamp(20px, 2vw, 25px); letter-spacing: -.035em; }
#cameraVideo {
    background: #f6f6f6; border: 1px solid #ececec; border-radius: 17px;
    box-shadow: none;
}
button {
    color: #fff; background: #ff5200; border: 1px solid #ff5200;
    border-radius: 12px; box-shadow: 0 5px 14px rgba(255,82,0,.14);
    transition: transform .18s ease, background .18s ease, box-shadow .18s ease;
}
button:hover { background: #e94b00; box-shadow: 0 8px 20px rgba(255,82,0,.18); }
button.secondary { color: #292a30; background: #fff; border: 1px solid #e4e4e4; box-shadow: none; }
button.secondary:hover { background: #fff4ee; border-color: #ffc5a8; }
.status { color: #737680; }
#status { color: #595c64; background: #fff8f4; border: 1px solid #ffe1d2; }
.scan-status { color: #a83900; border: 1px solid #ffd4bf; background: rgba(255,248,244,.97); box-shadow: 0 6px 24px rgba(0,0,0,.06); }
#loadingBar { background: rgba(255,82,0,.10); }
#loadingBar .progress { background: linear-gradient(90deg, #ff5200, #ff9b65, #ff5200); box-shadow: 0 0 16px rgba(255,82,0,.4); }
.metrics { gap: 12px; }
.metric {
    padding: 18px; border-radius: 17px; background: #fff;
    border: 1px solid #ededed; box-shadow: 0 3px 12px rgba(0,0,0,.025);
}
.metric:hover { transform: translateY(-2px); border-color: #ffc5a8; background: #fffaf7; }
.metric span { color: #282930; }
.metric strong { color: #6b6d75; }
.metric.category-card {
    border-color: #ffc5a8;
    background: linear-gradient(135deg, #fff0e6, #fffaf7 70%);
    padding: clamp(30px, 5vw, 64px) 28px;
    min-height: 280px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 14px;
    box-shadow: 0 12px 34px rgba(255,82,0,.09);
}
.metric.category-card span {
    color: #e94b00;
    font-size: clamp(13px, 1.4vw, 17px);
    font-weight: 800;
    letter-spacing: .16em;
    text-align: center;
}
.metric.category-card strong {
    color: #25262c;
    font-size: clamp(34px, 5vw, 64px);
    line-height: 1.08;
    max-width: 100%;
    text-align: center;
    margin-top: 0;
}
.metric.category-card small {
    color: #6d5a50;
    font-size: clamp(15px, 1.5vw, 19px);
    line-height: 1.65;
    max-width: 1000px;
    text-align: center;
}
.empty-state { color: #70737c; border: 1px dashed #dedede; background: #fafafa; }
pre { color: #393b42; background: #fafafa; border: 1px solid #ececec; }
.modal { background: rgba(22,23,26,.62); backdrop-filter: blur(8px); }
.modal-panel { color: #202127; border: 1px solid #ededed; background: #fff; box-shadow: 0 25px 80px rgba(0,0,0,.2); }
.canvas-wrap { background: #f4f4f4; border-color: #e5e5e5; }
::selection { background: rgba(255,82,0,.18); color: #202127; }
@media (max-width: 900px) { .layout { grid-template-columns: minmax(0,1fr); } }
@media (max-width: 560px) {
    header { padding: 18px 20px; }
    header p { margin-left: 0; }
    main { margin: 18px auto; padding: 0 13px 28px; }
    .layout { gap: 15px; }
    .card { border-radius: 18px; }
}

/* Final full-width, centered scanner layout */
html, body { width: 100%; min-height: 100%; overflow-x: hidden; }
header { width: 100%; padding: 22px clamp(16px, 3.2vw, 52px); }
header h1, header p { max-width: 1496px; margin-right: auto; margin-left: auto; }
header p { padding-left: 48px; }
main { max-width: 1600px; width: 100%; margin: 0 auto; padding: 30px clamp(16px, 3.2vw, 52px) 64px; }
.layout { display: flex; flex-direction: column; gap: 26px; align-items: stretch; }
#scannerSection, #dashboardSection { width: 100%; }
#scannerSection { text-align: center; }
#scannerSection h2, #scannerSection .status { text-align: left; }
#cameraVideo { display: block; width: 100%; height: min(70vh, 780px); min-height: 340px; max-height: 780px; object-fit: contain; margin: 0 auto; background: #f7f7f7; border-radius: 18px; }
#dashboardSection .metrics { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.metric.category-card { grid-column: 1 / -1; }

@media (max-width: 1000px) { #dashboardSection .metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); } #cameraVideo { height: 62vh; min-height: 300px; } }
@media (max-width: 650px) { main { padding: 18px 12px 32px; } header { padding: 18px 16px; } header p { padding-left: 0; } #cameraVideo { height: 48vh; min-height: 230px; } #dashboardSection .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } }



/* NutriScan — olive green + blush pink theme */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  color-scheme: light;
  --bg: #e9edda;
  --surface: #f4f6e9;
  --surface-strong: #fbf8f0;
  --line: #71804c;
  --text: #203522;
  --muted: #59654a;
  --mint: #788b4e;
  --cyan: #ee9cab;
  --shadow: 0 12px 30px rgba(46, 63, 34, .12);
}
html, body {
  background: #788b4e !important;
  color: #203522;
  scroll-behavior: smooth;
}
body {
  font-family: 'DM Sans', sans-serif;
  background:
    radial-gradient(ellipse at 8% 6%, rgba(238,156,171,.16), transparent 28%),
    radial-gradient(ellipse at 92% 16%, rgba(158,174,114,.20), transparent 30%),
    linear-gradient(145deg, #788b4e, #6d8045 58%, #82945a) !important;
  background-attachment: fixed;
}
header {
  position: relative;
  overflow: hidden;
  text-align: center;
  padding: 25px clamp(16px, 3.2vw, 52px) 22px;
  color: #203522;
  background: rgba(244,246,233,.88);
  border-bottom: 2px solid #53653c;
  box-shadow: 0 5px 22px rgba(46,63,34,.08);
  backdrop-filter: blur(14px);
}
header:after {
  display: block;
  content: '';
  position: absolute;
  width: 320px; height: 150px; right: 5%; top: -115px;
  background: #ee9cab; filter: blur(70px); opacity: .42;
  pointer-events: none;
}
header h1 {
  display: flex; justify-content: center; align-items: center; gap: 12px;
  margin: 0 auto; color: #263c28;
  font: 700 clamp(36px, 4vw, 54px)/1.08 'Space Grotesk', 'DM Sans', sans-serif;
  letter-spacing: -.045em; text-align: center;
}
header h1::first-letter { color: #788b4e; }
header p {
  max-width: 760px; margin: 10px auto 0 !important; padding: 0 !important;
  color: #59654a; font-size: clamp(14px, 1.3vw, 17px); text-align: center;
}
main { background: transparent; }
.card {
  color: #203522;
  background: rgba(244,246,233,.91);
  border: 1.5px solid #8c9a68;
  border-radius: 22px;
  box-shadow: 0 9px 26px rgba(46,63,34,.10);
  backdrop-filter: blur(10px);
}
h2 {
  color: #263c28;
  font-family: 'Space Grotesk', 'DM Sans', sans-serif;
  font-size: clamp(20px, 2.1vw, 28px);
  letter-spacing: -.035em;
}
#cameraVideo {
  background: #263c28;
  border: 2px solid #53653c;
  border-radius: 17px;
  box-shadow: 0 5px 0 rgba(83,101,60,.12);
}
button {
  color: #fffaf2;
  background: #596f3e;
  border: 1.5px solid #40552f;
  border-radius: 999px;
  box-shadow: 0 5px 12px rgba(65,85,47,.14);
  font-weight: 800;
  transition: transform .18s ease, background .18s ease, box-shadow .18s ease;
}
button:hover {
  color: #263c28; background: #ee9cab; border-color: #40552f;
  box-shadow: 3px 4px 0 rgba(64,85,47,.22);
}
button.secondary {
  color: #34442d; background: #f8e4e7;
  border: 1.5px solid #d98d9d; box-shadow: none;
}
button.secondary:hover { background: #ee9cab; border-color: #b86e7f; }
button:disabled { opacity: .48; }
.status { color: #59654a; }
#status, .scan-status {
  color: #31452c;
  background: #f8e4e7;
  border: 1.5px solid #d98d9d;
  border-radius: 14px;
  box-shadow: none;
}
#loadingBar {
  height: 7px; opacity: 0;
  background: rgba(238,156,171,.28);
  border-bottom: 1px solid #53653c;
  box-shadow: 0 2px 0 rgba(32,53,34,.08);
}
#loadingBar.active { opacity: 1; }
#loadingBar .progress {
  height: 100%; width: 38%; border-radius: 0 8px 8px 0;
  background: linear-gradient(90deg, #596f3e, #9eae72, #ee9cab);
  box-shadow: 0 0 14px rgba(120,139,78,.35);
  animation-duration: 1s;
}
.metrics { gap: 12px; }
.metric {
  color: #203522;
  padding: 18px;
  border-radius: 17px;
  background: #fbf8f0;
  border: 1.5px solid #c2cba8;
  box-shadow: 0 4px 12px rgba(46,63,34,.055);
}
.metric:hover {
  transform: translateY(-2px);
  border-color: #d98d9d;
  background: #f9e8eb;
}
.metric span { color: #263c28; }
.metric strong { color: #59654a; }
.metric.category-card {
  background: linear-gradient(125deg, #cbd6ae, #e2e8ce 64%, #f8dfe4);
  color: #203522;
  border: 2px solid #53653c;
  border-radius: 19px;
  box-shadow: 5px 6px 0 rgba(46,63,34,.10);
  padding: clamp(30px, 5vw, 64px) 28px;
  min-height: 280px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center; gap: 14px;
}
.metric.category-card span {
  color: #53653c;
  font-family: 'Space Grotesk', 'DM Sans', sans-serif;
  font-size: clamp(13px, 1.4vw, 17px);
  font-weight: 800; letter-spacing: .14em; text-align: center;
}
.metric.category-card strong {
  color: #203522;
  font-family: 'Space Grotesk', 'DM Sans', sans-serif;
  font-size: clamp(38px, 6vw, 76px);
  line-height: 1.02; letter-spacing: -.04em;
  max-width: 100%; text-align: center; margin-top: 0;
}
.metric.category-card small {
  color: #46543a; font-size: clamp(15px, 1.5vw, 19px);
  line-height: 1.65; max-width: 1000px; text-align: center;
}
.empty-state {
  color: #59654a; background: #f7f8ee;
  border: 1.5px dashed #9aa77b; border-radius: 16px;
}
pre { color: #34442d; background: #f7f8ee; border: 1px solid #c2cba8; }
.modal { background: rgba(28,43,27,.62); backdrop-filter: blur(9px); }
.modal-panel {
  color: #203522; background: #f4f6e9;
  border: 1.5px solid #8c9a68; border-radius: 22px;
  box-shadow: 0 25px 80px rgba(24,39,23,.25);
}
.canvas-wrap { background: #e4e9d1; border-color: #9aa77b; }
#cropCanvas { outline-color: #ee9cab; }
::selection { background: #ee9cab; color: #203522; }
@media (max-width: 650px) {
  header { padding: 20px 14px; }
  header h1 { font-size: clamp(32px, 8vw, 42px); }
  .card { border-radius: 17px; }
  button { padding: 11px 14px; }
}


/* Swiggy-inspired food category strip for NutriScan's header */
.nutriscan-header {
  min-height: 162px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 1.45fr) minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 20px clamp(18px, 3vw, 44px) 19px !important;
  position: relative;
  overflow: hidden;
}
.nutriscan-header .header-brand {
  position: relative;
  z-index: 2;
  min-width: 0;
  text-align: center;
}
.nutriscan-header .header-brand h1 {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  font-size: clamp(34px, 3.7vw, 52px);
  white-space: nowrap;
}
.nutriscan-header .brand-bowl {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: .88em;
  filter: drop-shadow(0 5px 3px rgba(31, 61, 39, .18));
}
.nutriscan-header .header-brand p {
  max-width: 620px;
  margin: 9px auto 0 !important;
  text-align: center;
  line-height: 1.4;
}
.header-food-strip {
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  gap: clamp(5px, 1vw, 16px);
  min-width: 0;
  height: 100%;
  position: relative;
  z-index: 1;
}
.food-float {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  min-width: 0;
  text-align: center;
  animation: foodBob 4s ease-in-out infinite;
}
.food-float:nth-child(2) { animation-delay: -.8s; }
.food-float:nth-child(3) { animation-delay: -1.6s; }
.food-float:nth-child(4) { animation-delay: -2.4s; }
.food-float > span {
  display: block;
  font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
  font-size: clamp(28px, 3vw, 43px);
  line-height: 1.15;
  filter: drop-shadow(0 7px 3px rgba(45, 59, 32, .18));
  transition: transform .2s ease, filter .2s ease;
}
.food-float:hover > span {
  transform: translateY(-5px) scale(1.12) rotate(-4deg);
  filter: drop-shadow(0 10px 5px rgba(45, 59, 32, .22));
}
.food-float small {
  color: #59654a;
  font-size: clamp(9px, .8vw, 11px);
  font-weight: 700;
  letter-spacing: .01em;
  white-space: nowrap;
}
.food-avocado > span { transform: rotate(-9deg); }
.food-berry > span { transform: rotate(8deg); }
.food-nuts > span { transform: rotate(-7deg); }
.food-greens > span { transform: rotate(7deg); }
.food-egg > span { transform: rotate(-7deg); }
.food-banana > span { transform: rotate(8deg); }
.food-choco > span { transform: rotate(-6deg); }
.food-oats > span { transform: rotate(5deg); }
@keyframes foodBob {
  0%, 100% { translate: 0 0; }
  50% { translate: 0 -5px; }
}
@media (max-width: 1000px) {
  .nutriscan-header {
    grid-template-columns: minmax(0, .8fr) minmax(300px, 1.5fr) minmax(0, .8fr);
    padding-left: 14px !important;
    padding-right: 14px !important;
  }
  .food-float > span { font-size: clamp(24px, 3vw, 34px); }
  .food-float small { display: none; }
}
@media (max-width: 720px) {
  .nutriscan-header {
    grid-template-columns: 1fr;
    gap: 9px;
    padding: 17px 14px 15px !important;
  }
  .nutriscan-header .header-brand { grid-row: 1; }
  .nutriscan-header .header-brand h1 { font-size: clamp(32px, 8vw, 42px); }
  .header-food-strip {
    grid-row: 2;
    justify-content: center;
    gap: clamp(15px, 5vw, 34px);
    min-height: 42px;
  }
  .header-food-right { display: none; }
  .food-float > span { font-size: 27px; }
  .food-float small { display: block; font-size: 9px; }
}
@media (prefers-reduced-motion: reduce) {
  .food-float { animation: none; }
}


/* Subtle geometric texture + translucent content panels */
body {
  background-color: #788b4e !important;
  background-image:
    radial-gradient(circle at 14% 22%, rgba(74, 91, 45, .20) 0 1.5px, transparent 2px),
    radial-gradient(circle at 80% 66%, rgba(74, 91, 45, .16) 0 1.5px, transparent 2px),
    linear-gradient(135deg, transparent 0 47%, rgba(74, 91, 45, .12) 47.2% 47.8%, transparent 48%),
    linear-gradient(45deg, transparent 0 47%, rgba(74, 91, 45, .10) 47.2% 47.8%, transparent 48%),
    linear-gradient(145deg, #788b4e, #6d8045 58%, #82945a) !important;
  background-size: 34px 34px, 46px 46px, 90px 90px, 120px 120px, auto !important;
  background-attachment: fixed !important;
}

/* Main page cards: slightly translucent so the olive backdrop softly shows through */
.card {
  background: rgba(244, 246, 233, .84) !important;
  backdrop-filter: blur(7px);
  -webkit-backdrop-filter: blur(7px);
  border-color: rgba(140, 154, 104, .9);
}

/* Keep modal/popup appearance unchanged as requested */
.modal-panel {
  background: #f4f6e9 !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  opacity: 1 !important;
}

/* Extra restrained geometric shapes on the page background only */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  opacity: .48;
  background:
    linear-gradient(30deg, transparent 48%, rgba(74, 91, 45, .13) 49%, rgba(74, 91, 45, .13) 50%, transparent 51%) 0 0 / 170px 150px,
    linear-gradient(150deg, transparent 48%, rgba(74, 91, 45, .10) 49%, rgba(74, 91, 45, .10) 50%, transparent 51%) 35px 22px / 210px 180px,
    radial-gradient(ellipse at 20% 70%, rgba(74, 91, 45, .10), transparent 34%),
    radial-gradient(ellipse at 86% 24%, rgba(74, 91, 45, .10), transparent 32%);
}


/* Minimal creator credit at the bottom of the page */
.site-footer {
    width: 100%;
    padding: 26px 16px 32px;
    text-align: center;
    color: #203522;
    background: rgba(244, 246, 233, .88);
    border-top: 2px solid #53653c;
    box-shadow: 0 -5px 22px rgba(46, 63, 34, .07);
}
.site-footer .made-by {
    display: block;
    margin-bottom: 5px;
    color: #59654a;
    font-size: 14px;
    font-style: italic;
    letter-spacing: .04em;
}
.site-footer .creator-name {
    display: block;
    color: #263c28;
    font-family: 'Space Grotesk', 'DM Sans', sans-serif;
    font-size: clamp(17px, 2vw, 21px);
    font-weight: 700;
    line-height: 1.55;
}
@media (max-width: 560px) {
    .site-footer { padding: 22px 14px 26px; }
}

</style>
</head>
<body>
<div id="loadingBar" aria-hidden="true"><div class="progress"></div></div>
<header class="nutriscan-header">
    <div class="header-food-strip header-food-left" aria-hidden="true">
        <span class="food-float food-avocado"><span>🥑</span><small>Healthy fats</small></span>
        <span class="food-float food-berry"><span>🍓</span><small>Vitamins</small></span>
        <span class="food-float food-nuts"><span>🥜</span><small>Protein</small></span>
        <span class="food-float food-greens"><span>🥦</span><small>Fibre</small></span>
    </div>
    <div class="header-brand">
        <h1><span class="brand-bowl" aria-hidden="true">🥗</span> NutriScan</h1>
        <p>AI-powered nutrition label recognition with dynamic nutrient cards</p>
    </div>
    <div class="header-food-strip header-food-right" aria-hidden="true">
        <span class="food-float food-egg"><span>🥚</span><small>Protein</small></span>
        <span class="food-float food-banana"><span>🍌</span><small>Energy</small></span>
        <span class="food-float food-choco"><span>🍫</span><small>Snacks</small></span>
        <span class="food-float food-oats"><span>🥣</span><small>Whole grains</small></span>
    </div>
</header>
<main>
<div id="scanProgressStatus" class="scan-status" role="status" aria-live="polite">Connecting to AI and analyzing the nutrition label…</div>
<div class="layout">
<section class="card" id="scannerSection">
    <h2>Live camera scanner</h2>
    <video id="cameraVideo" autoplay playsinline muted aria-label="Live camera feed"></video>
    <p class="status" id="status">Starting camera...</p>
    <button onclick="openCropTool()">Capture frame &amp; crop label</button>
    <button class="secondary" onclick="scanFullFrame()">Scan full frame</button>
    <button class="secondary" onclick="location.reload()">Restart feed</button>
    <p class="status">For best results, fill the frame with the nutrition table, keep it flat, and avoid glare. Use “Capture frame &amp; crop label” to select just the table.</p>
</section>
<section class="card" id="dashboardSection">
    <h2>Nutrition dashboard</h2>
    <p class="status">Values are extracted from the visible label. Always verify them against the original packaging.</p>
    <div class="metrics" id="dynamicMetrics">
        <div class="empty-state">Scan a nutrition label to display the readings found on that package. Each scan replaces these cards with the new label's contents.</div>
    </div>
</section>
</div>
</main>
<footer class="site-footer">
    <span class="made-by">made by</span>
    <span class="creator-name">Anahita Singh</span>
    <span class="creator-name">Aryan Dutta purkayastha</span>
</footer>

<div class="modal" id="cropModal" role="dialog" aria-modal="true" aria-labelledby="cropTitle">
  <div class="modal-panel">
    <h2 id="cropTitle">Crop the nutrition table</h2>
    <p class="status">Drag across the image to draw a rectangle around the nutrition facts table. Include the text and numbers, but exclude surrounding packaging where possible.</p>
    <div class="canvas-wrap"><canvas id="cropCanvas"></canvas></div>
    <p class="status" id="cropStatus">Take a snapshot, then drag to select the label.</p>
    <div class="modal-actions">
      <button onclick="scanCrop()">Scan selected area</button>
      <button class="secondary" onclick="clearSelection()">Clear selection</button>
      <button class="secondary" onclick="closeCropTool()">Cancel</button>
    </div>
  </div>
</div>

<script>
const cameraVideo = document.getElementById("cameraVideo");
const cropCanvas = document.getElementById("cropCanvas");
const cropCtx = cropCanvas.getContext("2d");
const cropStatus = document.getElementById("cropStatus");
const cropModal = document.getElementById("cropModal");
let snapshotCanvas = document.createElement("canvas");
let selection = null;
let dragStart = null;
let isDragging = false;

function setStatus(message) {
    document.getElementById("status").textContent = message;
}


async function startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setStatus("Camera access is not supported here. Open NutriScan over HTTPS in a modern browser.");
        return;
    }
    try {
        setStatus("Requesting camera permission…");
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: false,
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        });
        cameraVideo.srcObject = stream;
        await cameraVideo.play();
        setStatus("Camera ready. Position the nutrition label inside the frame.");
    } catch (error) {
        console.error("Camera start failed:", error);
        setStatus("Could not start the camera. Allow camera permission in your browser and make sure the site uses HTTPS.");
    }
}
window.addEventListener("beforeunload", () => {
    if (cameraVideo.srcObject) {
        cameraVideo.srcObject.getTracks().forEach(track => track.stop());
    }
});

function openCropTool() {
    if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) {
        setStatus("Camera frame is not ready yet. Wait a moment and try again.");
        return;
    }

    // Freeze the currently displayed camera frame into a snapshot.
    snapshotCanvas.width = cameraVideo.videoWidth;
    snapshotCanvas.height = cameraVideo.videoHeight;
    snapshotCanvas.getContext("2d").drawImage(
        cameraVideo, 0, 0, snapshotCanvas.width, snapshotCanvas.height
    );

    cropCanvas.width = snapshotCanvas.width;
    cropCanvas.height = snapshotCanvas.height;
    cropCtx.drawImage(snapshotCanvas, 0, 0);
    selection = null;
    dragStart = null;
    isDragging = false;
    cropStatus.textContent = "Drag a rectangle around only the nutrition facts table.";
    cropModal.classList.add("open");
}

function closeCropTool() {
    cropModal.classList.remove("open");
}

function canvasPoint(event) {
    const rect = cropCanvas.getBoundingClientRect();
    return {
        x: Math.max(0, Math.min(cropCanvas.width,
            (event.clientX - rect.left) * cropCanvas.width / rect.width)),
        y: Math.max(0, Math.min(cropCanvas.height,
            (event.clientY - rect.top) * cropCanvas.height / rect.height))
    };
}

function redrawSelection(currentPoint = null) {
    cropCtx.clearRect(0, 0, cropCanvas.width, cropCanvas.height);
    cropCtx.drawImage(snapshotCanvas, 0, 0);

    const box = selection || (dragStart && currentPoint ? {
        x: Math.min(dragStart.x, currentPoint.x),
        y: Math.min(dragStart.y, currentPoint.y),
        w: Math.abs(currentPoint.x - dragStart.x),
        h: Math.abs(currentPoint.y - dragStart.y)
    } : null);

    if (box && box.w > 0 && box.h > 0) {
        cropCtx.fillStyle = "rgba(0, 0, 0, 0.35)";
        cropCtx.fillRect(0, 0, cropCanvas.width, cropCanvas.height);
        cropCtx.clearRect(box.x, box.y, box.w, box.h);
        cropCtx.drawImage(
            snapshotCanvas, box.x, box.y, box.w, box.h,
            box.x, box.y, box.w, box.h
        );
        cropCtx.strokeStyle = "#39e079";
        cropCtx.lineWidth = Math.max(3, cropCanvas.width / 500);
        cropCtx.strokeRect(box.x, box.y, box.w, box.h);
    }
}

cropCanvas.addEventListener("pointerdown", event => {
    event.preventDefault();
    cropCanvas.setPointerCapture(event.pointerId);
    dragStart = canvasPoint(event);
    selection = null;
    isDragging = true;
});

cropCanvas.addEventListener("pointermove", event => {
    if (!isDragging) return;
    redrawSelection(canvasPoint(event));
});

cropCanvas.addEventListener("pointerup", event => {
    if (!isDragging) return;
    const end = canvasPoint(event);
    selection = {
        x: Math.round(Math.min(dragStart.x, end.x)),
        y: Math.round(Math.min(dragStart.y, end.y)),
        w: Math.round(Math.abs(end.x - dragStart.x)),
        h: Math.round(Math.abs(end.y - dragStart.y))
    };
    isDragging = false;
    dragStart = null;
    redrawSelection();
    cropStatus.textContent = selection.w > 30 && selection.h > 30
        ? "Crop selected. Click “Scan selected area”."
        : "Selection is too small. Drag a larger rectangle around the table.";
});

function clearSelection() {
    selection = null;
    dragStart = null;
    isDragging = false;
    cropCtx.clearRect(0, 0, cropCanvas.width, cropCanvas.height);
    cropCtx.drawImage(snapshotCanvas, 0, 0);
    cropStatus.textContent = "Selection cleared. Drag around the nutrition table.";
}

async function scanCrop() {
    if (!selection || selection.w < 30 || selection.h < 30) {
        cropStatus.textContent = "First drag a rectangle around the nutrition table.";
        return;
    }

    const crop = document.createElement("canvas");
    crop.width = selection.w;
    crop.height = selection.h;
    crop.getContext("2d").drawImage(
        snapshotCanvas,
        selection.x, selection.y, selection.w, selection.h,
        0, 0, selection.w, selection.h
    );

    cropStatus.textContent = "Scanning cropped label...";
    const blob = await new Promise(resolve => crop.toBlob(resolve, "image/png"));
    if (!blob) {
        cropStatus.textContent = "Could not create the crop. Please try again.";
        return;
    }

    const formData = new FormData();
    formData.append("image", blob, "nutrition-crop.png");
    await sendScanRequest(formData);
    closeCropTool();
}

async function scanFullFrame() {
    if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) {
        setStatus("Camera frame is not ready yet. Wait a moment and try again.");
        return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    canvas.getContext("2d").drawImage(cameraVideo, 0, 0);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
    const formData = new FormData();
    formData.append("image", blob, "full-frame.png");
    await sendScanRequest(formData);
}

function renderDynamicDashboard(rows, category = null) {
    const container = document.getElementById("dynamicMetrics");
    container.replaceChildren();
    if (!rows.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "No clear label/value rows were detected. Try a tighter crop, better lighting, or a straighter angle. Try a tighter crop, better lighting, or a straighter angle.";
        container.appendChild(empty);
    }
    rows.forEach((row, index) => {
        const card = document.createElement("div");
        card.className = "metric";
        const label = document.createElement("span");
        label.textContent = row.label || `Recognized line ${index + 1}`;
        const value = document.createElement("strong");
        value.textContent = row.value || row.text;
        card.append(label, value);
        container.appendChild(card);
    });
    // Show the AI food classification after the extracted nutrient readings.
    if (category && category.label) {
        const categoryCard = document.createElement("div");
        categoryCard.className = "metric category-card";
        const categoryLabel = document.createElement("span");
        categoryLabel.textContent = "AI food classification";
        const categoryValue = document.createElement("strong");
        categoryValue.textContent = category.label;
        categoryCard.append(categoryLabel, categoryValue);
        if (category.reason) {
            const reason = document.createElement("small");
            reason.textContent = category.reason;
            categoryCard.appendChild(reason);
        }
        container.appendChild(categoryCard);
    }
}

function setScanLoading(isLoading) {
    const bar = document.getElementById("loadingBar");
    const status = document.getElementById("scanProgressStatus");
    bar.classList.toggle("active", isLoading);
    document.body.classList.toggle("is-loading", isLoading);
    status.classList.toggle("visible", isLoading);
    if (isLoading) {
        status.textContent = "Analyzing label with AI… This can take a few seconds.";
        setStatus("Sending the selected label to the AI service…");
    }
}

async function sendScanRequest(formData) {
    setScanLoading(true);
    try {
        const response = await fetch("/scan", {method: "POST", body: formData});
        let data;
        try {
            data = await response.json();
        } catch (_) {
            throw new Error("The server returned an invalid response.");
        }
        if (!response.ok) {
            throw new Error(data.error || `Scan request failed (${response.status}).`);
        }
        renderDynamicDashboard(data.rows || [], data.category || null);
        setStatus(data.error || "Scan complete. Please verify the extracted text against the package.");
        document.getElementById("dashboardSection").scrollIntoView({behavior: "smooth", block: "start"});
    } catch (error) {
        setStatus(error.message || "Could not scan. Check that the Flask server is running.");
    } finally {
        setScanLoading(false);
    }
}
startCamera();
</script>
</body>
</html>
"""

def parse_nutrition(text):
    result = {
        "calories": "",
        "protein": "",
        "carbs": "",
        "fat": "",
        "sugar": "",
        "sodium": "",
    }

    normalized = text.lower().replace(",", ".")
    normalized = normalized.replace("—", "-").replace("–", "-")

    patterns = {
        "calories": (
            r"(?:energy|calories|kcal)\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*(?:kcal|cal)?"
        ),
        "protein": (
            r"protein(?:s)?\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*(?:g|gm|grams?)?\b"
        ),
        "carbs": (
            r"(?:total\s+)?carbohydrates?"
            r"\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:g|gm)?\b"
        ),
        "fat": (
            r"(?:total\s+)?fat\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*(?:g|gm)?\b"
        ),
        "sugar": (
            r"(?:total\s+)?sugars?"
            r"\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:g|gm)?\b"
        ),
        "sodium": (
            r"sodium\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*(?:mg|g)?\b"
        ),
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            result[key] = match.group(1)

    return result



def extract_dynamic_rows(text):
    """Turn OCR lines into flexible label/value cards without fixed nutrient categories."""
    rows = []
    seen = set()
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip(" |\t:;-")
        if len(line) < 2:
            continue
        # Keep only meaningful rows; nutrition labels often put several values on a line.
        numbers = list(re.finditer(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?", line))
        if numbers:
            first_number = numbers[0]
            label = line[:first_number.start()].strip(" :|-=\t")
            value = line[first_number.start():].strip(" :|-=\t")
            # If OCR starts a row with a number, keep the complete row instead of guessing a label.
            if not label or not re.search(r"[A-Za-z]{2}", label):
                label = "Nutrition reading"
                value = line
        else:
            # Include headings (e.g. Vitamins, Minerals, Per serving) as readable text cards too.
            label = line[:70]
            value = line
        key = (label.lower(), value.lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append({"label": label[:100], "value": value[:220], "text": line[:220]})
    return rows[:80]


def run_ocr(image):
    """Run several OCR passes and choose the result most likely to contain label text."""
    if image is None or image.size == 0:
        return ""

    # Upscale the selected crop; a tight crop gives OCR less irrelevant detail.
    height, width = image.shape[:2]
    scale = max(2, min(4, 1800 // max(width, height, 1)))
    enlarged = cv2.resize(
        image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY) if len(enlarged.shape) == 3 else enlarged
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    sharpened = cv2.addWeighted(
        enhanced, 1.6, cv2.GaussianBlur(enhanced, (0, 0), 2), -0.6, 0
    )
    _, otsu = cv2.threshold(
        sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    adaptive = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 11
    )

    candidates = []
    # Nutrition labels are usually table-like; psm 6, 11 and  a single text line mode
    # can produce different useful results.
    for processed in (gray, enhanced, sharpened, otsu, adaptive):
        for psm in (6, 11, 12):
            try:
                result = pytesseract.image_to_string(
                    processed, config=f"--oem 3 --psm {psm}"
                ).strip()
                if result:
                    candidates.append(result)
            except Exception as exc:
                print("Optional Tesseract OCR unavailable:", exc)
                break

    keywords = (
        "energy", "calories", "protein", "carbohydrate", "carbohydrates",
        "fat", "sugar", "sodium", "nutrition", "serving", "kcal",
        "nutritional", "saturated", "cholesterol"
    )

    def score(text):
        lower = text.lower()
        words = re.findall(r"[a-zA-Z]{2,}", lower)
        digits = re.findall(r"\d+(?:\.\d+)?", lower)
        keyword_hits = sum(lower.count(word) for word in keywords)
        # Reward nutrition terms and numeric values, not just lots of random letters.
        return keyword_hits * 30 + len(digits) * 8 + len(words) * 1.2

    return max(candidates, key=score) if candidates else ""




def analyze_with_groq(image):
    """Read a nutrition-label image with Groq's vision-capable chat API."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Set it in the terminal before starting NutriScan.")
    if image is None or image.size == 0:
        raise ValueError("The image is empty.")

    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not ok:
        raise RuntimeError("Could not encode the captured image.")
    image_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
    prompt = """
Read only the nutrition facts table visible in this image. Return ONLY valid JSON in this shape:
{"product_name":"","serving_size":"","rows":[{"label":"Energy","value":"120 kcal"}],"category":{"label":"High-fat profile","reason":"Fat is relatively prominent in the visible nutrition information."},"recognized_text":"","notes":""}
Include every legible row, including calories/energy, fats and subtypes, carbohydrates and sugars, fibre, protein, salt/sodium, vitamins, minerals, and percentages. Preserve units and printed values. If multiple columns exist, label them (per serving/per 100 g). Never invent or calculate values. Ignore background objects. If unclear, say so in notes and omit guessed rows. If no nutrition table is readable, return rows as an empty array and set category.label to "Unable to classify" with a brief reason.

Also classify the food's nutrition profile from the readable label values. Choose one concise category label from these options where supported: "High-fat profile", "High-sugar profile", "High-sodium profile", "Protein-rich profile", "Higher-fibre profile", "More balanced profile", or "Unable to classify". You may use a similarly clear category only if the evidence strongly supports it. In the reason, briefly explain which visible label values support the category; do not invent numbers or calculate missing values. Consider whether values are shown per serving or per 100 g when stated. Do not call a food simply "healthy" or "unhealthy" from one nutrient alone, and do not give medical advice. If the label does not provide enough context to make a reasonable classification, choose "Unable to classify".
"""
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "qwen/qwen3.8-27b",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]}],
            "temperature": 0.1,
            "max_completion_tokens": 3000,
            "response_format": {"type": "json_object"}
        },
        timeout=60
    )
    if not response.ok:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except (ValueError, AttributeError):
            detail = response.text
        raise RuntimeError(f"Groq API error ({response.status_code}): {detail}")
    try:
        result = json.loads(response.json()["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("Groq returned an unexpected response format.") from exc

    category_data = result.get("category", {})
    if not isinstance(category_data, dict):
        category_data = {}
    category = {
        "label": str(category_data.get("label", "Unable to classify")).strip()[:80] or "Unable to classify",
        "reason": str(category_data.get("reason", "The visible label did not provide enough information for a confident classification.")).strip()[:400],
    }

    rows = result.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    clean_rows, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        label, value = str(row.get("label", "")).strip(), str(row.get("value", "")).strip()
        if not label and not value:
            continue
        key = (label.lower(), value.lower())
        if key in seen:
            continue
        seen.add(key)
        clean_rows.append({"label": label[:100] or "Nutrition reading", "value": value[:220] or "Value not clearly readable", "text": f"{label}: {value}".strip(": ")[:320]})
    return {
        "product_name": str(result.get("product_name", "")).strip()[:150],
        "serving_size": str(result.get("serving_size", "")).strip()[:150],
        "category": category,
        "rows": clean_rows[:100],
        "recognized_text": str(result.get("recognized_text", "")).strip()[:12000],
        "notes": str(result.get("notes", "")).strip()[:1000]
    }


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/scan", methods=["POST"])
def scan():
    # The browser sends the captured crop (recommended) or the full camera frame.
    uploaded = request.files.get("image")
    if uploaded:
        file_bytes = np.frombuffer(uploaded.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({
                "text": "",
                "rows": [],
                "ai_used": False,
                "error": "Could not read the uploaded image. Please capture it again.",
            }), 400
    else:
        return jsonify({
            "text": "",
            "rows": [],
            "ai_used": False,
            "error": "No image was uploaded. Capture a frame or select a crop and try again.",
        }), 400

    # OCR runs locally as a fallback and provides text even if the API is unavailable.
    ocr_text = run_ocr(frame)
    try:
        ai_result = analyze_with_groq(frame)
        rows = ai_result["rows"]
        recognized_text = ai_result["recognized_text"] or ocr_text
        details = []
        if ai_result["product_name"]:
            details.append(f"Product: {ai_result['product_name']}")
        if ai_result["serving_size"]:
            details.append(f"Serving size: {ai_result['serving_size']}")
        if ai_result["notes"]:
            details.append(f"AI note: {ai_result['notes']}")
        if recognized_text:
            details.append(recognized_text)
        full_text = "\n".join(details) if details else "AI could not read clear text from this image."

        error = ""
        if not rows:
            error = "AI could not identify clear nutrient rows. Try a tighter crop, better lighting, or a straighter angle."
        elif ai_result["notes"]:
            error = f"AI scan complete. Please verify the label. Note: {ai_result['notes']}"
        else:
            error = "AI scan complete. Please verify all values against the original packaging."

        return jsonify({
            "text": full_text,
            "rows": rows,
            "ai_used": True,
            "product_name": ai_result["product_name"],
            "serving_size": ai_result["serving_size"],
            "category": ai_result["category"],
            "error": error,
        })

    except Exception as exc:
        print("Groq analysis failed; using OCR fallback:", exc)
        rows = extract_dynamic_rows(ocr_text)
        if not os.environ.get("GROQ_API_KEY", "").strip():
            message = "Groq API key not configured; showing OCR-only results. Set GROQ_API_KEY to enable AI."
        else:
            message = f"AI scan failed; showing OCR-only results. {str(exc)[:300]}"
        return jsonify({
            "text": ocr_text,
            "rows": rows,
            "ai_used": False,
            "error": message if ocr_text else message + " No readable OCR text was found; try a tighter crop and better lighting.",
        })


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
