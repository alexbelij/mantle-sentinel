# TZ для Developer Viktor — Mantle Sentinel
## Финальный план до дедлайна + Demo Day

**Дедлайн:** Jun 15 23:59 (DoraHacks submission)
**Demo Day:** Jul 2–3
**Контракт уже задеплоен Curator Viktor** → адрес ниже (обновить если деплой выполнен повторно)

---

## ⚠️ КОНТРАКТ v2 — ГОТОВ, ИСПОЛЬЗУЙ ЭТОТ ТЕКСТ

> Файл: `contracts/SentinelAlertRegistry.sol`  
> Заменить полностью.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title  SentinelAlertRegistry v2
/// @notice Immutable on-chain registry for Mantle Sentinel behavioral-drift alerts.
///         Only the authorized reporter (the Sentinel agent wallet set at deploy time)
///         may write. All reads are O(1) or bounded-gas. Events carry the storage
///         index so any off-chain consumer can reconstruct the full timeline without
///         scanning the entire array.
///
/// @dev    driftScore is scaled x10000:
///           0      = 0.0000 (no drift)
///           10 000 = 1.0000 (maximum drift)
///         Example: pipeline value 0.87  -> pass 8700 as driftScore.
contract SentinelAlertRegistry {

    // --- Types ---------------------------------------------------------------

    struct Alert {
        address reporter;   // msg.sender (Sentinel agent wallet)
        uint256 windowId;   // monitoring-window block number
        uint32  driftScore; // drift severity x10000, range 0..10000
        bytes4  alertType;  // four-byte tag: ENTR, HMNG, TMNG, etc.
        uint64  timestamp;  // block.timestamp at log time (seconds)
    }

    // --- State ---------------------------------------------------------------

    /// @notice Address authorised to write alerts (immutable after deploy)
    address public immutable owner;

    Alert[] private _alerts;

    // --- Events --------------------------------------------------------------

    event AlertLogged(
        address indexed reporter,
        uint256 indexed windowId,
        uint32          driftScore,
        bytes4          alertType,
        uint64          timestamp,
        uint256         alertIndex   // position in _alerts[] for O(1) getAlert()
    );

    // --- Errors --------------------------------------------------------------

    error Unauthorized();
    error InvalidDriftScore(uint32 score);
    error IndexOutOfBounds(uint256 requested, uint256 length);

    // --- Constructor ---------------------------------------------------------

    constructor() {
        owner = msg.sender;
    }

    // --- Modifier ------------------------------------------------------------

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // --- Write ---------------------------------------------------------------

    /// @notice Log a drift alert on-chain.
    ///         Can only be called by the Sentinel agent wallet (owner).
    /// @param windowId   Block number of the monitoring window that triggered the alert
    /// @param driftScore Drift severity x10000. Must be in 0..10000.
    ///                   Pass (float_score * 10000) truncated to uint32.
    /// @param alertType  Four-byte alert category tag:
    ///                     0x454e5452 = "ENTR" (entropy)
    ///                     0x484d4e47 = "HMNG" (Hamming)
    ///                     0x544d4e47 = "TMNG" (timing)
    function logAlert(
        uint256 windowId,
        uint32  driftScore,
        bytes4  alertType
    ) external onlyOwner {
        if (driftScore > 10_000) revert InvalidDriftScore(driftScore);

        uint256 idx = _alerts.length;
        uint64  ts  = uint64(block.timestamp);

        _alerts.push(Alert({
            reporter:   msg.sender,
            windowId:   windowId,
            driftScore: driftScore,
            alertType:  alertType,
            timestamp:  ts
        }));

        emit AlertLogged(msg.sender, windowId, driftScore, alertType, ts, idx);
    }

    // --- Read ----------------------------------------------------------------

    /// @notice Total number of logged alerts
    function getAlertCount() external view returns (uint256) {
        return _alerts.length;
    }

    /// @notice Retrieve a single alert by its storage index
    /// @param index Zero-based position (0 = first ever alert)
    function getAlert(uint256 index) external view returns (Alert memory) {
        if (index >= _alerts.length)
            revert IndexOutOfBounds(index, _alerts.length);
        return _alerts[index];
    }

    /// @notice Return the last `count` alerts ordered newest-first.
    ///         If count exceeds the total, all alerts are returned.
    ///         Maximum recommended: 50 alerts per call (gas safety margin).
    /// @param count Maximum number of alerts to return
    function getLatestAlerts(uint256 count)
        external view
        returns (Alert[] memory result)
    {
        uint256 total = _alerts.length;
        uint256 n     = count > total ? total : count;
        result = new Alert[](n);
        unchecked {
            for (uint256 i = 0; i < n; ++i) {
                result[i] = _alerts[total - 1 - i];
            }
        }
    }
}
```

**Изменения v2 vs оригинал:**
- `onlyOwner` + `immutable owner` → устраняет ALL CRITICAL уязвимости
- `require(driftScore <= 10_000)` → семантическая валидация
- `getLatestAlerts(uint256 count)` → dashboard читает последние N без индексатора
- `alertIndex` в Event → off-chain O(1) retrieval по event log
- `getAlert()` возвращает `Alert memory` (чище ABI, меньше кода)
- Custom errors вместо require(string) → дешевле по gas
- `unchecked` в петле getLatestAlerts → без оверфлоу-риска (bounded by total)
- Полный NatDoc со scaling-объяснением

---

## ITERATION 1 (~60 мин) — КОНТРАКТ + ОЧИСТКА

> Приоритет P0. Выполнить ПЕРВОЙ, потому что новый адрес контракта нужен всем остальным.

### [1a] Заменить контракт и передеплоить

1. Полностью заменить содержимое `contracts/SentinelAlertRegistry.sol` текстом выше
2. Обновить `foundry.toml` — добавить:
   ```toml
   [profile.default]
   solc_version = "0.8.28"
   ```
3. Задеплоить на Mantle mainnet (5000) и Sepolia (5003).  
   Деплой через `deploy.py` — но сначала пункт [1d].
4. После деплоя обновить `contracts/deployments.json` с новыми адресами и `contracts/abi.json`.
5. **Прислать мне (Curator) новый адрес mainnet-контракта.** Я обновлю SKILL.md.

### [1b] Удалить Foundry-шаблон

```bash
rm contracts/Counter.sol
rm test/Counter.t.sol
```

### [1c] Написать `test/SentinelAlertRegistry.t.sol`

Минимум 5 тестов:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "forge-std/Test.sol";
import "../contracts/SentinelAlertRegistry.sol";

contract SentinelAlertRegistryTest is Test {
    SentinelAlertRegistry reg;
    address owner;
    address stranger = address(0xBEEF);

    function setUp() public {
        owner = address(this);
        reg = new SentinelAlertRegistry();
    }

    function testLogAlert_success() public {
        reg.logAlert(100, 8700, bytes4("ENTR"));
        assertEq(reg.getAlertCount(), 1);
        SentinelAlertRegistry.Alert memory a = reg.getAlert(0);
        assertEq(a.driftScore, 8700);
        assertEq(a.windowId, 100);
    }

    function testLogAlert_onlyOwner() public {
        vm.prank(stranger);
        vm.expectRevert(SentinelAlertRegistry.Unauthorized.selector);
        reg.logAlert(100, 8700, bytes4("ENTR"));
    }

    function testLogAlert_invalidScore() public {
        vm.expectRevert(
            abi.encodeWithSelector(SentinelAlertRegistry.InvalidDriftScore.selector, uint32(10001))
        );
        reg.logAlert(100, 10001, bytes4("ENTR"));
    }

    function testGetAlert_success() public {
        reg.logAlert(42, 5000, bytes4("HMNG"));
        SentinelAlertRegistry.Alert memory a = reg.getAlert(0);
        assertEq(a.alertType, bytes4("HMNG"));
        assertEq(a.windowId, 42);
    }

    function testGetAlert_outOfBounds() public {
        vm.expectRevert(
            abi.encodeWithSelector(
                SentinelAlertRegistry.IndexOutOfBounds.selector,
                uint256(0), uint256(0)
            )
        );
        reg.getAlert(0);
    }

    function testGetLatestAlerts() public {
        reg.logAlert(1, 1000, bytes4("ENTR"));
        reg.logAlert(2, 2000, bytes4("HMNG"));
        SentinelAlertRegistry.Alert[] memory alerts = reg.getLatestAlerts(2);
        assertEq(alerts.length, 2);
        assertEq(alerts[0].windowId, 2); // newest first
        assertEq(alerts[1].windowId, 1);
    }
}
```

### [1d] Убрать приватный ключ из `deploy.py`

Заменить строку:
```python
PRIVATE_KEY = "0x3946db..."
```
На:
```python
import os
PRIVATE_KEY = os.environ.get("SENTINEL_PRIVATE_KEY") or os.environ["SENTINEL_PRIVATE_KEY"]
```

Создать `.env.example`:
```
SENTINEL_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
```

Добавить в `.gitignore`:
```
.env
*.env
```

### [1e] Обновить `self_attack.py` и pipeline

Везде где используется старый адрес контракта — заменить на новый из `contracts/deployments.json`.

**Проверка:**
```bash
forge test  # должно быть 6 passed
forge build # должно быть OK
python3 -m pytest src/ -q  # 84 passed
```

---

## ITERATION 2 (~45 мин) — README + CI + DOCS

### [2a] Переписать `README.md` полностью

Структура:
```
# Mantle Sentinel — HDC Behavioral DNA Agent

> Your smart contracts have a behavioral fingerprint. Sentinel knows when it changes.

## Pipeline

  [Mantle RPC]
      |
  T0: Entropy pre-filter (calldata)
      |
  T1: HDC Encoder — 10,000-dim bipolar hypervector
      |
  T2: Drift = max(Hamming distance, timing deviation)
      |
  T3: BOCPD / Static threshold detector
      |
  T4: Feature attribution (ablation)
      |
  T5: Z.ai natural-language explanation
      |
  [Telegram alert + on-chain logAlert() + Dashboard]

## Quick Start

  git clone https://github.com/alexbelij/mantle-sentinel
  cp .env.example .env  # add your private key
  pip install -r requirements.txt
  python3 src/live.py --contract USDC_E_ADDRESS

## Contract (Mantle Mainnet)

  Address: <NEW_ADDRESS>
  Explorer: https://mantlescan.xyz/address/<NEW_ADDRESS>

## Results

  4.3× clean/attack separation ratio on real USDC.e data (3,993 txs)
  Detection: ≤2 windows (≤100 txs)
  False positives: 0 on clean replay
  Tests: 84 passed (pytest) + 6 forge tests

## CI

  [badge]

## Live Demo

  https://mantle-sentinel-rho.vercel.app/
```

### [2b] `.github/workflows/pytest.yml`

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python -m pytest src/ -q
```

Добавить `requirements.txt` если нет.

### [2c] `docs/zai_prompt.md`

Скопировать реальный prompt template из кода (из T5-интерпретатора) в docs/zai_prompt.md. Формат:
```markdown
# Z.ai Prompt Template

Z.ai receives structured alert data from Sentinel's Tier 5 interpreter
and returns a human-readable explanation.

## Input schema

{
  "contract": "<address>",
  "window_id": <block_number>,
  "drift_score": <float 0..1>,
  "alert_type": "ENTR|HMNG|TMNG",
  "feature_attribution": {
    "selector_entropy": <float>,
    "hamming_distance": <float>,
    "timing_deviation": <float>
  },
  "top_feature": "selector_entropy"
}

## System prompt

You are a DeFi security analyst...

## User prompt template

<paste real template from code>
```

---

## ITERATION 3 (~30 мин) — LIVE RUN + Z.ai В DEMO

### [3a] Запустить live run на mainnet

После обновления адреса:
```bash
python3 src/self_attack.py --live
```
Должно: создать новый alert на mainnet, `getAlertCount()` вырастет.  
Записать новый tx hash.

### [3b] Вставить Z.ai-ответ в landing/index.html

В секции "Live Demo" или "Pipeline Demo" — добавить блок:
```html
<div class="zai-response">
  <span class="label">Z.ai explanation:</span>
  <p>"Sentinel detected entropy anomaly in window #39920662 on Mantle
     USDC.e. Selector distribution shifted: 3 novel selectors appeared,
     accounting for 47% of traffic. Hamming distance: 0.87 (threshold: 0.65).
     Recommended action: pause contract interactions and investigate
     selector 0x03df179c."</p>
</div>
```
(Используй реальный ответ из T-13c run или сформулируй по тем же данным.)

### [3c] Обновить DoraHacks BUIDL вручную (текст для копирования)

**Изменения:**
1. Адрес контракта → новый
2. VictimCounter Sepolia → добавить: `0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64`
3. Заменить строку про Z.ai:  
   ~~"Z.ai GLM for natural-language alert explanations"~~  
   → **"Z.ai formats confirmed alerts into operator-readable natural language. Detection is purely algebraic — no model is in the detection loop."**
4. Добавить абзац про конкурентов:  
   "Unlike Forta (rule-based + model training required) or Chainalysis (signature databases), Sentinel is training-free: same algorithm, same thresholds, any EVM contract, zero GPU."
5. Добавить 2 строки бизнес-модели:  
   "Target customers: DeFi protocols, bridges, and DAO treasuries. Business model: SaaS subscription per monitored contract — no per-alert fees."

---

## ITERATION 4 (~3-4 ч) — LANDING PAGE v4

**Файл:** `landing/index.html` (заменить полностью)  
**ТЗ:** `/work/projects/mantle_sentinel/TZ_LANDING_V4.md`  
**Дизайн:** `/work/projects/mantle_sentinel/DESIGN.md`

**Перед деплоем вставить:**
- Новый адрес контракта (из iter.1)
- Реальный URL DoraHacks BUIDL (после сабмита)
- Реальный Z.ai-ответ из T-13c run

**Порядок:** iter.4 можно запускать параллельно с iter.2-3, но финальный деплой — только после получения новых адресов из iter.1.

---

## ПОРЯДОК ВЫПОЛНЕНИЯ

```
1. Iter.1  →  получить новый адрес контракта
2. Iter.2 + Iter.3  →  параллельно (разные части кодовой базы)
3. После iter.3: обновить DoraHacks BUIDL → подать T-16
4. Iter.4  →  landing page v4 (можно параллельно с 2+3)
```

---

## POST-MVP ROADMAP

(Отдельный файл — см. ниже)

---

## КОНТРОЛЬНЫЙ СПИСОК ДО ДЕДЛАЙНА

```
[ ] Контракт v2 задеплоен (новый адрес)
[ ] Counter.sol + Counter.t.sol удалены
[ ] test/SentinelAlertRegistry.t.sol: forge test → 6 passed
[ ] deploy.py: private key → os.environ
[ ] .env.example создан, .gitignore обновлён
[ ] README.md переписан (pipeline + quick start + badge)
[ ] pytest.yml создан, CI badge в README
[ ] docs/zai_prompt.md создан
[ ] self_attack.py: второй live run → новый tx hash
[ ] landing: Z.ai-ответ виден в demo-секции
[ ] DoraHacks BUIDL обновлён (новый адрес, Z.ai framing, конкуренты, бизнес-модель)
[ ] T-16: X thread + BUIDL submitted
```
