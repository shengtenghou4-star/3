"""Cinematic, state-driven visual components for the presidential office.

The visual layer never invents simulation outcomes. It turns existing files, calls,
mandates, officials, meetings and press exchanges into a coherent working environment.
"""

from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


_STATUS_PHASE = {
    "awaiting_assignment": 0,
    "unassigned": 0,
    "assigned": 1,
    "on_track": 2,
    "delayed": 2,
    "narrowed": 2,
    "completed": 3,
    "partial": 3,
    "failed": 3,
    "withdrawn": 3,
}

_STATUS_TONE = {
    "awaiting_assignment": "amber",
    "unassigned": "red",
    "assigned": "blue",
    "on_track": "green",
    "delayed": "amber",
    "narrowed": "amber",
    "completed": "green",
    "partial": "amber",
    "failed": "red",
    "withdrawn": "slate",
}

_OFFICE_SIGILS = {
    "秘书长": "秘",
    "财务与准入总监": "财",
    "廉洁与纪律专员": "廉",
    "国家队技术总监": "技",
    "青训与校园足球专员": "青",
}

_OFFICE_TONES = {
    "秘书长": "gold",
    "财务与准入总监": "blue",
    "廉洁与纪律专员": "red",
    "国家队技术总监": "green",
    "青训与校园足球专员": "violet",
}


def inject_cinematic_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --fr-bg: #071019;
          --fr-panel: rgba(15, 29, 42, .86);
          --fr-panel-2: rgba(20, 38, 54, .72);
          --fr-line: rgba(168, 191, 211, .17);
          --fr-gold: #d9b96d;
          --fr-paper: #f1eadb;
          --fr-red: #a33b38;
          --fr-green: #65b98b;
          --fr-blue: #6fa8d5;
          --fr-text: #edf3f7;
          --fr-muted: #94a7b7;
          --fr-shadow: 0 26px 70px rgba(0,0,0,.34);
        }

        html, body, [class*="css"] {font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;}
        .stApp {
          background:
            radial-gradient(circle at 72% 8%, rgba(58, 91, 118, .18), transparent 27%),
            radial-gradient(circle at 18% 22%, rgba(132, 92, 48, .10), transparent 24%),
            linear-gradient(180deg, #071019 0%, #09131d 58%, #060d14 100%) !important;
        }
        .stApp::before {
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          opacity: .028;
          z-index: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.78' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.58'/%3E%3C/svg%3E");
        }
        [data-testid="stAppViewContainer"] > .main {position: relative; z-index: 1;}
        [data-testid="stHeader"] {background: rgba(7, 16, 25, .62); backdrop-filter: blur(16px);}
        [data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, rgba(17, 34, 49, .98), rgba(8, 18, 27, .99)),
            repeating-linear-gradient(90deg, rgba(255,255,255,.015) 0 1px, transparent 1px 4px) !important;
          border-right: 1px solid rgba(217,185,109,.18) !important;
          box-shadow: 16px 0 50px rgba(0,0,0,.22);
        }
        [data-testid="stSidebar"] h2 {letter-spacing: -.03em;}
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stDownloadButton > button {
          border: 1px solid rgba(217,185,109,.22);
          background: rgba(255,255,255,.045);
          color: #eef3f6;
        }
        [data-testid="stSidebar"] .stButton > button:hover,
        [data-testid="stSidebar"] .stDownloadButton > button:hover {
          border-color: rgba(217,185,109,.66);
          background: rgba(217,185,109,.09);
          transform: translateY(-1px);
        }

        .block-container {max-width: 1550px; padding-top: 1.2rem; padding-bottom: 5rem;}
        h1, h2, h3, h4 {letter-spacing: -.035em;}
        h3 {color: #f0f5f8;}
        hr {border-color: rgba(112,137,157,.22)!important;}

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
          gap: 7px;
          overflow-x: auto;
          padding: 7px;
          margin: 4px 0 20px;
          border: 1px solid rgba(168,191,211,.14);
          border-radius: 16px;
          background: rgba(9, 20, 30, .72);
          box-shadow: inset 0 1px 0 rgba(255,255,255,.035), 0 12px 34px rgba(0,0,0,.18);
          backdrop-filter: blur(14px);
        }
        [data-testid="stTabs"] button[role="tab"] {
          min-height: 42px;
          border-radius: 11px;
          color: #93a6b6;
          white-space: nowrap;
          transition: all .18s ease;
        }
        [data-testid="stTabs"] button[role="tab"]:hover {color: #f0f4f7; background: rgba(255,255,255,.045);}
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
          color: #101820;
          background: linear-gradient(180deg, #e4c87e, #cba85a);
          font-weight: 780;
          box-shadow: 0 8px 20px rgba(203,168,90,.22);
        }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {display: none;}

        .stButton > button, .stDownloadButton > button {
          min-height: 44px;
          border-radius: 11px;
          border: 1px solid rgba(135,159,180,.27);
          background: linear-gradient(180deg, rgba(27,48,66,.95), rgba(15,31,45,.95));
          color: #eef4f7;
          font-weight: 720;
          box-shadow: 0 8px 22px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.045);
          transition: transform .16s ease, border-color .16s ease, background .16s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
          transform: translateY(-2px);
          border-color: rgba(217,185,109,.72);
          color: #fff;
        }
        .stButton > button[kind="primary"] {
          color: #101820;
          border-color: #e2c577;
          background: linear-gradient(180deg, #e8cd86, #caa657);
          box-shadow: 0 12px 30px rgba(202,166,87,.24);
        }
        .stButton > button:disabled {opacity: .45; transform: none;}

        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div {
          color: #edf3f7;
          border-color: rgba(139,164,184,.27)!important;
          background: rgba(11,24,36,.88)!important;
          border-radius: 11px!important;
        }
        [data-testid="stRadio"] label {padding: 7px 10px; border-radius: 9px; transition: background .15s ease;}
        [data-testid="stRadio"] label:hover {background: rgba(255,255,255,.04);}
        [data-testid="stExpander"] {
          border: 1px solid rgba(137,161,181,.18)!important;
          border-radius: 13px!important;
          background: rgba(13,27,40,.62)!important;
          overflow: hidden;
        }
        [data-testid="stDataFrame"] {border: 1px solid rgba(137,161,181,.18); border-radius: 13px; overflow: hidden; box-shadow: 0 14px 30px rgba(0,0,0,.14);}
        [data-testid="stAlert"] {border-radius: 12px; border: 1px solid rgba(255,255,255,.08); box-shadow: 0 10px 22px rgba(0,0,0,.12);}

        .office-cinema {
          position: relative;
          overflow: hidden;
          min-height: 238px;
          display: grid;
          grid-template-columns: 118px minmax(0,1.5fr) minmax(280px,.8fr);
          gap: 24px;
          align-items: center;
          margin: 0 0 13px;
          padding: 25px 29px;
          border: 1px solid rgba(217,185,109,.24);
          border-radius: 22px;
          background:
            linear-gradient(112deg, rgba(25,48,66,.96) 0%, rgba(11,25,37,.97) 50%, rgba(8,18,28,.98) 100%);
          box-shadow: var(--fr-shadow), inset 0 1px 0 rgba(255,255,255,.045);
        }
        .office-cinema::before {
          content: "";
          position: absolute;
          inset: 0;
          pointer-events: none;
          background:
            radial-gradient(circle at 14% 20%, rgba(217,185,109,.13), transparent 24%),
            linear-gradient(90deg, transparent 0 74%, rgba(255,255,255,.018) 74% 74.3%, transparent 74.3% 100%);
        }
        .office-cinema::after {
          content: "";
          position: absolute;
          right: -75px;
          bottom: -115px;
          width: 330px;
          height: 330px;
          border: 1px solid rgba(217,185,109,.15);
          border-radius: 50%;
          box-shadow: 0 0 0 34px rgba(217,185,109,.025), 0 0 0 68px rgba(217,185,109,.016);
        }
        .office-crest {
          position: relative;
          z-index: 1;
          width: 105px;
          aspect-ratio: 1;
          display: grid;
          place-items: center;
          border: 1px solid rgba(229,202,135,.66);
          border-radius: 50%;
          color: #f0d995;
          background: radial-gradient(circle, rgba(217,185,109,.13), rgba(4,12,19,.48));
          box-shadow: inset 0 0 0 8px rgba(217,185,109,.035), 0 14px 30px rgba(0,0,0,.32);
          font-family: Georgia, serif;
          font-size: 2.15rem;
          font-weight: 800;
          letter-spacing: -.08em;
        }
        .office-crest small {position:absolute; bottom:15px; font: 650 .55rem/1 sans-serif; letter-spacing:.16em; color:#9cb0bf;}
        .office-copy {position:relative; z-index:1;}
        .office-eyebrow {color:#d9b96d; font-size:.69rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase;}
        .office-copy h1 {margin:7px 0 8px; color:#f3f7f9; font-size:clamp(2rem,4vw,3.45rem); line-height:1;}
        .office-copy p {margin:0; color:#a6b6c3; font-size:.96rem;}
        .office-copy .situation {margin-top:17px; max-width:800px; color:#e6edf1; font-size:1.02rem; line-height:1.65;}
        .office-date-card {position:relative; z-index:1; align-self:stretch; display:flex; flex-direction:column; justify-content:center; padding:20px 22px; border-left:1px solid rgba(217,185,109,.18);}
        .office-date-card .day {color:#f5f7f8; font-size:1.45rem; font-weight:780;}
        .office-date-card .place {margin-top:3px;color:#8fa2b1;font-size:.82rem;}
        .pressure-row {display:flex; flex-wrap:wrap; gap:7px; margin-top:17px;}
        .pressure-chip {display:inline-flex;align-items:center;gap:7px;padding:5px 9px;border:1px solid rgba(144,168,188,.22);border-radius:999px;background:rgba(255,255,255,.035);color:#aebcc8;font-size:.72rem;}
        .pressure-chip::before {content:"";width:7px;height:7px;border-radius:50%;background:#758a9b;box-shadow:0 0 0 4px rgba(117,138,155,.10);}
        .pressure-chip.amber::before {background:#d4ad59;box-shadow:0 0 0 4px rgba(212,173,89,.12);}
        .pressure-chip.red::before {background:#d56761;box-shadow:0 0 0 4px rgba(213,103,97,.12);}
        .pressure-chip.green::before {background:#65b98b;box-shadow:0 0 0 4px rgba(101,185,139,.12);}

        .desk-scene {
          position:relative;
          overflow:hidden;
          min-height:226px;
          margin:0 0 20px;
          padding:22px;
          border:1px solid rgba(128,151,171,.17);
          border-radius:18px;
          background:
            linear-gradient(180deg, rgba(7,15,23,.2), rgba(7,15,23,.75)),
            repeating-linear-gradient(96deg, #3b281b 0 44px, #4b3222 44px 88px, #342318 88px 132px);
          box-shadow:0 22px 48px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.035);
        }
        .desk-scene::before {content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.18),transparent 34%,transparent 66%,rgba(0,0,0,.2));pointer-events:none;}
        .desk-label {position:relative;z-index:1;color:#e5c87f;font-size:.7rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;}
        .desk-grid {position:relative;z-index:1;display:grid;grid-template-columns:1.25fr .78fr .88fr .85fr;gap:15px;align-items:end;margin-top:18px;}
        .desk-object {position:relative;min-height:136px;padding:17px;border:1px solid rgba(255,255,255,.14);border-radius:12px;background:linear-gradient(160deg,rgba(21,34,43,.88),rgba(9,18,25,.92));box-shadow:0 14px 26px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.04);}
        .desk-object h4 {margin:25px 0 5px;color:#f0f4f6;font-size:1rem;}
        .desk-object p {margin:0;color:#8fa0ad;font-size:.78rem;line-height:1.45;}
        .folder-stack::before,.folder-stack::after {content:"";position:absolute;left:13px;right:13px;height:9px;border-radius:4px 4px 1px 1px;background:#d8c99e;box-shadow:0 1px 0 rgba(0,0,0,.24);}
        .folder-stack::before {top:13px;transform:rotate(-1.2deg);}
        .folder-stack::after {top:20px;left:18px;right:9px;background:#ae3e3a;transform:rotate(.8deg);}
        .phone-object::before {content:"";position:absolute;top:17px;left:18px;width:52px;height:18px;border:5px solid #912f2d;border-bottom-width:8px;border-radius:20px 20px 10px 10px;transform:rotate(-4deg);box-shadow:0 4px 10px rgba(0,0,0,.35);}
        .phone-object::after {content:"";position:absolute;top:43px;left:27px;width:37px;height:27px;border-radius:8px;background:#762625;box-shadow:inset 0 1px 0 rgba(255,255,255,.12);}
        .press-object::before {content:"";position:absolute;top:14px;left:17px;width:58px;height:39px;border:3px solid #607f96;border-radius:5px;background:linear-gradient(180deg,#17364a,#0b1d2a);box-shadow:0 5px 12px rgba(0,0,0,.35);}
        .press-object::after {content:"LIVE";position:absolute;top:24px;left:30px;color:#e66b65;font-size:.65rem;font-weight:900;letter-spacing:.1em;}
        .mandate-object::before {content:"";position:absolute;top:15px;left:20px;width:50px;height:39px;border-radius:5px;background:#e5decf;transform:rotate(-2deg);box-shadow:0 5px 12px rgba(0,0,0,.35);}
        .mandate-object::after {content:"督办";position:absolute;top:27px;left:31px;color:#8f2f2d;font-size:.72rem;font-weight:900;transform:rotate(-2deg);}
        .object-badge {position:absolute;right:11px;top:10px;min-width:24px;height:24px;padding:0 7px;display:grid;place-items:center;border-radius:999px;color:#101820;background:#d9b96d;font-size:.7rem;font-weight:900;box-shadow:0 6px 14px rgba(217,185,109,.24);}

        .mandate-lifecycle {display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:15px 0 18px;}
        .life-step {position:relative;padding:12px 10px 12px 35px;border:1px solid rgba(134,158,178,.16);border-radius:10px;background:rgba(255,255,255,.025);color:#708493;font-size:.76rem;}
        .life-step::before {content:"";position:absolute;left:12px;top:50%;width:10px;height:10px;border-radius:50%;background:#465968;transform:translateY(-50%);box-shadow:0 0 0 5px rgba(70,89,104,.10);}
        .life-step.done {color:#aebdc8;border-color:rgba(101,185,139,.22);}
        .life-step.done::before {background:#65b98b;box-shadow:0 0 0 5px rgba(101,185,139,.10);}
        .life-step.current {color:#f0f4f6;border-color:rgba(217,185,109,.55);background:rgba(217,185,109,.07);}
        .life-step.current::before {background:#d9b96d;box-shadow:0 0 0 6px rgba(217,185,109,.12);animation:pulse 1.8s ease-in-out infinite;}
        .life-step.red.current {border-color:rgba(213,103,97,.55);background:rgba(213,103,97,.07);}
        .life-step.red.current::before {background:#d56761;box-shadow:0 0 0 6px rgba(213,103,97,.12);}

        .official-portrait {display:grid;grid-template-columns:68px 1fr;gap:15px;align-items:center;margin:12px 0;padding:15px;border:1px solid rgba(141,164,184,.18);border-radius:14px;background:linear-gradient(145deg,rgba(21,39,54,.88),rgba(10,22,32,.88));box-shadow:0 12px 28px rgba(0,0,0,.17);}
        .portrait-sigil {width:64px;height:72px;display:grid;place-items:center;border-radius:10px 10px 23px 23px;color:#101820;background:linear-gradient(180deg,#e7cf91,#bd9450);font-family:Georgia,serif;font-size:1.7rem;font-weight:900;box-shadow:inset 0 -10px 20px rgba(0,0,0,.14),0 9px 18px rgba(0,0,0,.22);}
        .portrait-sigil.blue {background:linear-gradient(180deg,#8ec0e4,#537f9f);}
        .portrait-sigil.red {background:linear-gradient(180deg,#d98580,#98514d);}
        .portrait-sigil.green {background:linear-gradient(180deg,#8bcda9,#4f8e6d);}
        .portrait-sigil.violet {background:linear-gradient(180deg,#b39bd4,#715d91);}
        .official-copy h4 {margin:0;color:#f0f4f6;font-size:1.12rem;}
        .official-copy .role {color:#d9b96d;font-size:.75rem;}
        .official-copy .public-state {margin-top:5px;color:#91a4b3;font-size:.78rem;}

        .report-document {position:relative;min-height:272px;padding:19px 18px 17px;border-radius:4px 4px 12px 4px;color:#1d252b;background:#ece7da;box-shadow:0 17px 34px rgba(0,0,0,.28);transform:rotate(-.35deg);}
        .report-document::before {content:"";position:absolute;top:0;left:0;right:0;height:6px;background:#a7894b;}
        .report-document.blue::before {background:#537f9f;}
        .report-document.red::before {background:#98514d;}
        .report-document.green::before {background:#4f8e6d;}
        .report-document.violet::before {background:#715d91;}
        .report-document h4 {margin:11px 0 7px;color:#1d252b;font-size:1.05rem;}
        .report-document p {color:#3f474c;font-size:.82rem;line-height:1.52;}
        .report-document .doc-kicker {color:#775e2e;font-size:.64rem;font-weight:850;letter-spacing:.09em;text-transform:uppercase;}
        .report-document .doc-author {margin-top:5px;color:#6c7378;font-size:.72rem;}
        .report-document .doc-note {padding-top:10px;border-top:1px solid rgba(38,47,53,.16);color:#5b6267;font-size:.75rem;}

        .meeting-room {position:relative;overflow:hidden;padding:25px;border:1px solid rgba(150,174,193,.16);border-radius:18px;background:linear-gradient(145deg,rgba(17,34,49,.94),rgba(7,17,25,.96));box-shadow:var(--fr-shadow);}
        .meeting-room::before {content:"";position:absolute;left:12%;right:12%;bottom:-52px;height:150px;border-radius:50%;background:linear-gradient(180deg,#573822,#2c1d14);box-shadow:0 -7px 18px rgba(0,0,0,.35);}
        .meeting-heads {position:relative;z-index:1;display:grid;grid-template-columns:1fr 115px 1fr;gap:22px;align-items:center;}
        .meeting-person {text-align:center;}
        .person-head {width:72px;height:72px;margin:0 auto 10px;display:grid;place-items:center;border:2px solid rgba(217,185,109,.28);border-radius:50%;color:#e9d18f;background:radial-gradient(circle,#2a4458,#0f2433);font-size:1.2rem;font-weight:900;box-shadow:0 12px 26px rgba(0,0,0,.28);}
        .person-name {color:#f0f5f7;font-weight:800;}
        .person-role {color:#8ea1af;font-size:.74rem;}
        .meeting-center {text-align:center;color:#d9b96d;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;}
        .meeting-center::before {content:"";display:block;width:52px;height:52px;margin:0 auto 8px;border:1px solid rgba(217,185,109,.38);border-radius:50%;background:radial-gradient(circle,rgba(217,185,109,.14),transparent);}
        .meeting-opening {position:relative;z-index:1;margin:25px auto 4px;max-width:920px;padding:17px 21px;border-left:4px solid #d9b96d;color:#e7eef2;background:rgba(255,255,255,.035);font-family:Georgia,"Songti SC",serif;font-size:1.06rem;line-height:1.65;}

        .press-stage {position:relative;overflow:hidden;min-height:230px;padding:25px 28px;border:1px solid rgba(142,165,184,.18);border-radius:18px;background:linear-gradient(180deg,#112b3e 0%,#0b1b29 56%,#071019 100%);box-shadow:var(--fr-shadow);}
        .press-stage::before {content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% -10%,rgba(205,227,241,.18),transparent 35%),linear-gradient(90deg,transparent 49.8%,rgba(255,255,255,.035) 50%,transparent 50.2%);}
        .press-banner {position:relative;z-index:1;text-align:center;color:#8fa6b6;font-size:.69rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase;}
        .podium {position:relative;z-index:1;width:150px;height:104px;margin:21px auto 0;padding-top:28px;text-align:center;color:#d9b96d;background:linear-gradient(180deg,#2a475b,#122a3b);clip-path:polygon(15% 0,85% 0,100% 100%,0 100%);box-shadow:0 15px 30px rgba(0,0,0,.28);font-family:Georgia,serif;font-size:1.1rem;font-weight:900;}
        .microphones {position:absolute;z-index:2;top:51px;left:50%;width:72px;height:28px;transform:translateX(-50%);}
        .microphones::before,.microphones::after {content:"";position:absolute;top:0;width:6px;height:38px;border-radius:5px;background:#1c252c;transform-origin:bottom;}
        .microphones::before {left:20px;transform:rotate(-22deg);}
        .microphones::after {right:20px;transform:rotate(22deg);}
        .reporter-row {position:relative;z-index:1;display:flex;justify-content:center;gap:18px;margin-top:15px;}
        .reporter {width:34px;height:34px;border-radius:50% 50% 42% 42%;background:#243846;box-shadow:0 22px 0 8px #182a37;opacity:.86;}
        .press-topic {position:relative;z-index:1;margin-top:26px;text-align:center;color:#eef4f7;font-size:1.05rem;font-weight:780;}
        .press-sub {position:relative;z-index:1;margin-top:4px;text-align:center;color:#8da0af;font-size:.78rem;}
        .exchange {position:relative;margin:14px 0;padding:15px 18px;border-radius:13px;background:rgba(17,34,48,.78);border:1px solid rgba(140,163,183,.16);}
        .exchange.reporter {margin-right:8%;border-left:4px solid #6e96b4;}
        .exchange.president {margin-left:8%;border-left:4px solid #d9b96d;background:rgba(38,48,53,.74);}
        .exchange-label {color:#8fa5b5;font-size:.69rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;}
        .exchange blockquote {margin:7px 0 0;color:#edf3f6;font-size:.98rem;line-height:1.6;}
        .exchange-consequence {margin-top:8px;color:#8da0ae;font-size:.75rem;}

        @keyframes pulse {0%,100%{transform:translateY(-50%) scale(1);opacity:1}50%{transform:translateY(-50%) scale(1.14);opacity:.76}}
        @keyframes rise {from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
        .office-cinema,.desk-scene,.meeting-room,.press-stage,.report-document,.official-portrait {animation:rise .38s ease both;}

        @media (max-width: 1000px) {
          .office-cinema {grid-template-columns:90px 1fr;}
          .office-crest {width:82px;font-size:1.65rem;}
          .office-date-card {grid-column:1/-1;border-left:0;border-top:1px solid rgba(217,185,109,.16);padding:15px 0 0;}
          .desk-grid {grid-template-columns:repeat(2,1fr);}
          .meeting-heads {grid-template-columns:1fr 80px 1fr;}
        }
        @media (max-width: 660px) {
          .block-container {padding-left:.75rem;padding-right:.75rem;}
          .office-cinema {grid-template-columns:1fr;padding:21px;}
          .office-crest {display:none;}
          .office-copy h1 {font-size:2.15rem;}
          .desk-grid {grid-template-columns:1fr 1fr;gap:10px;}
          .desk-object {min-height:125px;padding:13px;}
          .mandate-lifecycle {grid-template-columns:1fr 1fr;}
          .meeting-heads {grid-template-columns:1fr 55px 1fr;gap:8px;}
          .person-head {width:58px;height:58px;}
          .press-stage {padding:20px 13px;}
          .reporter-row {gap:10px;}
          .reporter {width:28px;height:28px;}
          .exchange.reporter {margin-right:0;}
          .exchange.president {margin-left:0;}
        }
        @media (prefers-reduced-motion: reduce) {
          *,*::before,*::after {animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_cinematic_header(game, packet) -> None:
    active_mandates = list(game.executive.active_mandates())
    unassigned = sum(item.status in {"awaiting_assignment", "unassigned"} for item in active_mandates)
    delayed = sum(item.status in {"delayed", "narrowed"} for item in active_mandates)
    open_press = sum(item.status == "open" for item in game.executive.press_sessions)
    pressures: list[tuple[str, str]] = []
    if game.current_decision is not None:
        pressures.append(("red", "主席亲签件待批"))
    if unassigned:
        pressures.append(("red", f"{unassigned}项决定无人负责"))
    if delayed:
        pressures.append(("amber", f"{delayed}项执行延误或缩水"))
    if game.office.leaks:
        pressures.append(("red", "存在泄密后果"))
    if open_press:
        pressures.append(("amber", "发布会仍在进行"))
    if not pressures:
        pressures.append(("green", "办公室运行平稳"))

    chips = "".join(
        f'<span class="pressure-chip {escape(tone)}">{escape(label)}</span>'
        for tone, label in pressures[:5]
    )
    role = (
        f"现任国家足球协会主席 · {escape(game.player_name)}"
        if game.can_act
        else f"{escape(game.player_name)}主席生涯档案 · 当前由{escape(game.current_president.name)}执政"
    )
    st.markdown(
        f"""
        <section class="office-cinema">
          <div class="office-crest">FR<small>协会印</small></div>
          <div class="office-copy">
            <div class="office-eyebrow">National Football Association · Presidential Office</div>
            <h1>国家足协主席办公室</h1>
            <p>{role}</p>
            <div class="situation"><b>秘书长晨间判断：</b>{escape(packet.situation_line)}</div>
            <div class="pressure-row">{chips}</div>
          </div>
          <div class="office-date-card">
            <div class="office-eyebrow">Chairman's Daily Book</div>
            <div class="day">{escape(packet.date_label)} · {escape(packet.weekday_label)}</div>
            <div class="place">{escape(packet.office_location)}<br>第{game.term_index}届任期 · 本届M{game.local_month}</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_desk_scene(game, packet) -> None:
    active = list(game.executive.active_mandates())
    dossier_count = 1 if packet.dossier is not None else 0
    correspondence_count = len(packet.correspondence)
    press_count = len(packet.press_clippings)
    mandate_count = len(active)
    dossier_copy = "一份红头呈签件正等待主席本人落笔" if dossier_count else "普通行政件已由秘书处分流"
    call_copy = "有机构正通过正式或敏感渠道寻求主席回应" if correspondence_count else "红线电话暂时安静"
    press_copy = "媒体联络官已准备可能的追问与口径风险" if press_count else "舆情屏没有新的高压议题"
    mandate_copy = "签过的文件正在由具名官员承担结果" if mandate_count else "暂无执行中的重大主席授权"
    st.markdown(
        f"""
        <section class="desk-scene">
          <div class="desk-label">President's Desk · 今日桌面</div>
          <div class="desk-grid">
            <div class="desk-object folder-stack">
              <span class="object-badge">{dossier_count}</span>
              <h4>主席收文盘</h4><p>{escape(dossier_copy)}</p>
            </div>
            <div class="desk-object phone-object">
              <span class="object-badge">{correspondence_count}</span>
              <h4>红线电话</h4><p>{escape(call_copy)}</p>
            </div>
            <div class="desk-object press-object">
              <span class="object-badge">{press_count}</span>
              <h4>舆情屏</h4><p>{escape(press_copy)}</p>
            </div>
            <div class="desk-object mandate-object">
              <span class="object-badge">{mandate_count}</span>
              <h4>督办文件夹</h4><p>{escape(mandate_copy)}</p>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_mandate_lifecycle(mandate, status_label: str) -> None:
    current = _STATUS_PHASE.get(mandate.status, 0)
    tone = _STATUS_TONE.get(mandate.status, "slate")
    labels = ("主席签署", "具名授权", "部门执行", "督查复核")
    steps = []
    for index, label in enumerate(labels):
        state = "done" if index < current else "current" if index == current else ""
        if state == "current" and tone == "red":
            state += " red"
        steps.append(f'<div class="life-step {state}">{escape(label)}</div>')
    st.markdown(
        '<div class="mandate-lifecycle">' + "".join(steps) + "</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"当前节点：{status_label}")


def render_official_portrait(office: str, official_name: str, public_state: str) -> None:
    sigil = _OFFICE_SIGILS.get(office, escape(official_name[:1] if official_name else "官"))
    tone = _OFFICE_TONES.get(office, "gold")
    st.markdown(
        f"""
        <div class="official-portrait">
          <div class="portrait-sigil {escape(tone)}">{escape(sigil)}</div>
          <div class="official-copy">
            <div class="role">{escape(office)}</div>
            <h4>{escape(official_name)}</h4>
            <div class="public-state">{escape(public_state)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_report_document(report) -> None:
    tone = _OFFICE_TONES.get(report.office, "gold")
    st.markdown(
        f"""
        <article class="report-document {escape(tone)}">
          <div class="doc-kicker">{escape(report.urgency)} · {escape(report.office)}</div>
          <h4>{escape(report.headline)}</h4>
          <div class="doc-author">呈报人：{escape(report.official_name)} · 判断把握：{escape(report.confidence)}</div>
          <p><b>建议：</b>{escape(report.recommendation)}</p>
          <p><b>材料依据：</b>{escape(report.evidence)}</p>
          <div class="doc-note"><b>可能盲点：</b>{escape(report.blind_spot)}</div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def render_meeting_room(game, meeting) -> None:
    visitor_initial = meeting.visitor[:1] if meeting.visitor else "客"
    chairman_initial = game.player_name[:1] if game.player_name else "主"
    st.markdown(
        f"""
        <section class="meeting-room">
          <div class="meeting-heads">
            <div class="meeting-person">
              <div class="person-head">{escape(chairman_initial)}</div>
              <div class="person-name">{escape(game.player_name)}</div>
              <div class="person-role">国家足协主席</div>
            </div>
            <div class="meeting-center">第三会客室<br>{escape(meeting.requested_duration)}</div>
            <div class="meeting-person">
              <div class="person-head">{escape(visitor_initial)}</div>
              <div class="person-name">{escape(meeting.visitor)}</div>
              <div class="person-role">{escape(meeting.institution)}</div>
            </div>
          </div>
          <div class="meeting-opening">“{escape(meeting.opening_line)}”</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_press_stage(session) -> None:
    status = "正在直播" if session.status == "open" else "发布会已结束"
    reporters = '<span class="reporter"></span>' * 7
    st.markdown(
        f"""
        <section class="press-stage">
          <div class="press-banner">National Football Association · Press Room</div>
          <div class="microphones"></div>
          <div class="podium">FR</div>
          <div class="reporter-row">{reporters}</div>
          <div class="press-topic">{escape(session.topic)}</div>
          <div class="press-sub">{escape(session.outlet)} · {escape(status)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_press_exchange(exchange) -> None:
    st.markdown(
        f"""
        <div class="exchange reporter">
          <div class="exchange-label">记者 · 第{exchange.round_number}轮</div>
          <blockquote>{escape(exchange.question)}</blockquote>
        </div>
        <div class="exchange president">
          <div class="exchange-label">主席公开答复</div>
          <blockquote>“{escape(exchange.quote)}”</blockquote>
          <div class="exchange-consequence">{escape(exchange.consequence)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def office_tone(office: str) -> str:
    return _OFFICE_TONES.get(office, "gold")


def office_sigil(office: str) -> str:
    return _OFFICE_SIGILS.get(office, "官")
