SHELL := /usr/bin/env bash

# ==== Notify targets (policy) ====
.PHONY: notify notify-done notify-done-site notify-local notify-test progress

# 使い方:
#   make notify MSG="メッセージ" TITLE="タイトル"
#   サブタイトルやアクション等は EXTRA に渡す:
#   make notify MSG="OK?" TITLE="確認" \
#       EXTRA="-S '選択してください' -a 'OK,Cancel'"

MSG   ?= デフォルトメッセージ
TITLE ?= 通知
EXTRA ?=
# 通知シンク: gate(既定) / file / both
NOTIFY_SINK ?= gate
# 通知の堅牢化: ゲート送信に加え、ローカルtalker(直送)もフォールバックで試行
NOTIFY_FALLBACK_LOCAL ?= 1

notify:
	set -euo pipefail; \
	[ -f .env ] && set -a && . ./.env && set +a || true; \
	if [ "${SUPPRESS_NOTIFY:-0}" = "1" ] || [ "${JOB_CLASS:-}" = "fast" ]; then \
	  echo '[notify] SUPPRESS_NOTIFY=1 or JOB_CLASS=fast → 通知をスキップします'; \
	  exit 0; \
	fi; \
	if [ "$(NOTIFY_SINK)" = "gate" ]; then \
	  NOTICE_SYNC=1 NOTICE_SLACK_SYNC=1 NOTICE_SLACK_VERBOSE=1 NOTICE_SLACK_STDOUT=1 ./scripts/notice.sh ${DIRECT:+-d} ${BASE:+-u $(BASE)} -m "$(MSG)" -t "$(TITLE)" $(EXTRA) || true; \
	  if [ "$(NOTIFY_FALLBACK_LOCAL)" = "1" ]; then \
	    LB=$${NOTICE_BASE_URL:-}; \
	    if [ -z "$$LB" ] && [ -n "$$NOTICE_TARGET" ]; then LB="http://$${NOTICE_TARGET#@}"; fi; \
	    if [ -n "$$LB" ]; then \
	      echo "[notify] fallback: direct -> $$LB"; \
	      NOTICE_DIRECT=1 NOTICE_SYNC=1 ./scripts/notice.sh -u "$$LB" -m "$(MSG)" -t "$(TITLE)" $(EXTRA) || true; \
	    fi; \
	  fi; \
	elif [ "$(NOTIFY_SINK)" = "file" ]; then \
	  ./scripts/notice_to_file.sh -m "$(MSG)" -t "$(TITLE)"; \
	else \
	  NOTICE_SYNC=1 NOTICE_SLACK_SYNC=1 NOTICE_SLACK_VERBOSE=1 NOTICE_SLACK_STDOUT=1 ./scripts/notice.sh ${DIRECT:+-d} ${BASE:+-u $(BASE)} -m "$(MSG)" -t "$(TITLE)" $(EXTRA) || true; \
	  ./scripts/notice_to_file.sh -m "$(MSG)" -t "$(TITLE)"; \
	fi

# 直近の実行メモ(memo/run_*.md)から概要を抽出し通知
PUBLISH_TIMEOUT ?= 180
AUTO_PUBLISH_ASYNC ?= 1

notify-done:
	set -euo pipefail; \
	[ -f .env ] && set -a && . ./.env && set +a || true; \
	if [ "${SUPPRESS_NOTIFY:-0}" = "1" ] || [ "${JOB_CLASS:-}" = "fast" ]; then \
	  echo '[notify-done] SUPPRESS_NOTIFY=1 or JOB_CLASS=fast → 通知をスキップします'; \
	  exit 0; \
	fi; \
	FILE=$$(ls -t memo/run_*.md 2>/dev/null | head -n1 || true); \
	if [ -n "$$FILE" ]; then \
	  TITLE="作業完了: $$(basename "$$FILE" .md)"; \
	  SUMMARY=$${MSG_PRE:-}$$'\n'$$(awk '/^## 結果サマリ/{flag=1;next}/^## /{if(flag) exit}flag' "$$FILE" | sed 's/^/- /' | head -n 6 || true); \
	  OUTS=$$(awk '/^## 生成物/{flag=1;next}/^## /{if(flag) exit}flag' "$$FILE" | sed 's/^/- /' | head -n 4 || true); \
	  NEXT=$$(awk '/^## 次アクション/{flag=1;next}/^## /{if(flag) exit}flag' "$$FILE" | sed 's/^/- /' | head -n 3 || true); \
	  MSG="結果:\n$${SUMMARY}\n成果物:\n$${OUTS}\n次の一手:\n$${NEXT}"; \
	else \
	  TITLE="作業完了"; MSG="結果: 変更を反映しレポートを再生成しました\n成果物: server/public/reports/index.html"; \
	fi; \
	if [ "$(NOTIFY_SINK)" = "gate" ]; then \
	  NOTICE_SYNC=1 NOTICE_SLACK_SYNC=1 NOTICE_SLACK_VERBOSE=1 NOTICE_SLACK_STDOUT=1 ./scripts/notice.sh ${DIRECT:+-d} ${BASE:+-u $(BASE)} -m "$$MSG" -t "$$TITLE" || true; \
	  if [ "$(NOTIFY_FALLBACK_LOCAL)" = "1" ]; then \
	    LB=$${NOTICE_BASE_URL:-}; if [ -z "$$LB" ] && [ -n "$$NOTICE_TARGET" ]; then LB="http://$${NOTICE_TARGET#@}"; fi; \
	    if [ -n "$$LB" ]; then \
	      echo "[notify-done] fallback: direct -> $$LB"; \
	      NOTICE_DIRECT=1 NOTICE_SYNC=1 ./scripts/notice.sh -u "$$LB" -m "$$MSG" -t "$$TITLE" || true; \
	    fi; \
	  fi; \
	elif [ "$(NOTIFY_SINK)" = "file" ]; then \
	  ./scripts/notice_to_file.sh -m "$$MSG" -t "$$TITLE"; \
	else \
	  NOTICE_SYNC=1 NOTICE_SLACK_SYNC=1 NOTICE_SLACK_VERBOSE=1 NOTICE_SLACK_STDOUT=1 ./scripts/notice.sh ${DIRECT:+-d} ${BASE:+-u $(BASE)} -m "$$MSG" -t "$$TITLE" || true; \
	  ./scripts/notice_to_file.sh -m "$$MSG" -t "$$TITLE"; \
	fi
	@# オプション: AUTO_PUBLISH_SITE が指定されていればサイト更新も実施
	@if [ -n "$(AUTO_PUBLISH_SITE)" ]; then \
	  echo "AUTO_PUBLISH_SITE=1: publish-site + web-deploy を実行"; \
	  if [ "$(AUTO_PUBLISH_ASYNC)" = "1" ]; then \
	    ( $(MAKE) publish-site >/dev/null 2>&1 && $(MAKE) web-deploy >/dev/null 2>&1 ) & \
	    disown || true; \
	    echo "dispatched site publish/deploy in background"; \
	  else \
	    if command -v timeout >/dev/null 2>&1; then \
	      timeout $(PUBLISH_TIMEOUT)s $(MAKE) publish-site || echo '[warn] publish-site timed out'; \
	      timeout $(PUBLISH_TIMEOUT)s $(MAKE) web-deploy   || echo '[warn] web-deploy timed out'; \
	    else \
	      $(MAKE) publish-site; $(MAKE) web-deploy; \
	    fi; \
	  fi; \
	fi

# 通知とサイト更新を一括実行（標準運用の拡張）
notify-done-site:
	$(MAKE) notify-done AUTO_PUBLISH_SITE=1

notify-local:
	$(MAKE) notify DIRECT=1

# 送信経路の健全性チェック（直接送信・同期）
notify-test:
	set -euo pipefail; \
	[ -f .env ] && set -a && . ./.env && set +a || true; \
	NOTICE_DIRECT=1 NOTICE_SYNC=1 ./scripts/notice.sh -m "送信経路テスト(直接)" -t "テスト" || true; \
	./scripts/notice.sh -m "送信経路テスト(ゲート)" -t "テスト" -S "到達性" -a "OK" || true

# 進捗更新とSOTA再生成
RATE ?=
NOTE ?=
progress:
	set -euo pipefail; \
	[ -n "$(RATE)" ] || { echo 'RATE を0..100で指定してください' >&2; exit 1; }; \
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/update_progress.py --rate $(RATE) --note "$(NOTE)"; \
	# Generate CV pages (μ(k) grids) for clean/LSB/HSB
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/clean_for_fit.txt --out-prefix cv_shared_summary; \
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/lsb_noBL.txt --out-prefix cv_shared_summary_lsb_noBL; \
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/hsb_noBL.txt --out-prefix cv_shared_summary_hsb_noBL; \
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py; \
	echo 'updated SOTA with progress'

# 研究方針指示者への質問を追加してSOTA再生成
.PHONY: ask-lead
Q ?=
WHO ?=
ask-lead:
	set -euo pipefail; \
	[ -n "$(Q)" ] || { echo 'Q に質問本文を指定してください' >&2; exit 1; }; \
	PYTHONPATH=. ./.venv/bin/python scripts/add_question_to_lead.py "$(Q)" --who "$(WHO)"; \
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py; \
	echo 'added question and rebuilt SOTA'

# ==== Dev/site targets ====
PY := .venv/bin/python
PIP := .venv/bin/pip
RUNPY := $(if $(wildcard .venv/bin/python),$(PY),python3)

# Memory-safety defaults for heavy Python tasks (override by setting MEMSAFE_ENV="")
MEMSAFE_ENV ?= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2

.PHONY: setup lint test dev fit global-fit build all docs paper-sota site serve publish-site figs fit-all artifacts site-audit

setup:
	python3 -m venv .venv
	$(PIP) install -U pip
	$(PIP) install numpy scipy pandas matplotlib

lint:
	@echo "(lint) 導入済みリンターが無いためスキップ"

test:
	PYTHONPATH=. ./.venv/bin/python -m pytest -q

dev:
	@echo "仮想環境を有効化: source .venv/bin/activate"

fit:
	PYTHONPATH=. $(PY) scripts/fit_sparc_fdb3.py

global-fit:
	PYTHONPATH=. $(PY) scripts/global_fit_fdb3.py

build:
	@echo "ビルド対象無し。論文は paper/Makefile を使用。"

all: setup
	bash scripts/fetch_sparc.sh
	PYTHONPATH=. $(PY) scripts/fit_sparc_fdb3_all.py
	PYTHONPATH=. $(PY) scripts/global_fit_fdb3.py
	PYTHONPATH=. $(PY) scripts/plot_sota_figs.py
	bash scripts/sync_figs_to_paper.sh
	bash scripts/sync_figs_to_docs.sh
	mkdocs build --strict

figs:
	PYTHONPATH=. $(PY) scripts/plot_sota_figs.py

fit-all:
	bash scripts/fit_all.sh

artifacts:
	@ls -1 data/artifacts 2>/dev/null || echo "no artifacts yet"

.PHONY: cosmo-formal
cosmo-formal:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_cosmo_formal.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'cosmology formal cards generated and SOTA rebuilt'

.PHONY: repro
repro:
	PYTHONPATH=. $(RUNPY) scripts/repro.py

.PHONY: repro-local
repro-local:
	PYTHONPATH=. $(RUNPY) scripts/benchmarks/run_ngc3198_fullbench.py
	PYTHONPATH=. $(RUNPY) scripts/benchmarks/run_ngc2403_fullbench.py
	PYTHONPATH=. $(RUNPY) scripts/eu/class_validate.py
	PYTHONPATH=. $(RUNPY) scripts/repro_local_checks.py

# ===== Rep6 (Surface vs Volumetric) =====
.PHONY: rep6-recalc
rep6-recalc:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/compare_surface_vs_volumetric.py
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'rep6 recalculated and SOTA rebuilt'

.PHONY: rep6-info
rep6-info:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/compare_ws_vs_phieta.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'rep6 info-flow vs surface compared and SOTA rebuilt'

.PHONY: rep6
rep6:
	PYTHONPATH=. ./.venv/bin/python scripts/figs/plot_rep6.py --all --out assets/rep6 --force-template v2
	PYTHONPATH=. ./.venv/bin/python scripts/reports/inject_rep6_figs.py --in server/public/reports/ws_vs_phieta_rep6.html --imgs assets/rep6
	@# publish rep6 assets under web root so relative links work from SOTA/reports
	mkdir -p server/public/assets/rep6
	cp -f assets/rep6/*.{png,svg} server/public/assets/rep6/ 2>/dev/null || true
	echo 'rep6 figures generated and injected'

.PHONY: rep6-ab-fast rep6-ab-full
rep6-ab-fast:
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py \
	  --fast --downsample 2 --float32 --psf-sigma 1.0 1.5 \
	  --hipass 8-16 --errfloor 0.03,3,7 --k 2 --rng 42 --s 0.4 0.6 1.0 \
	  --workers-auto
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py \
	  --fast --downsample 2 --float32 --psf-sigma 1.0 1.5 \
	  --hipass 8-16 --errfloor 0.03,3,7 --k 2 --rng 42 \
	  --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2
	  --workers-auto
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/reports/build_ws_vs_phieta_rep6.py \
	  --ws-json data/results/rep6_ws_fast.json \
	  --if-json data/results/rep6_phieta_fast.json \
	  --fair-json data/results/ws_vs_phieta_fair_best.json \
	  --out server/public/reports/ws_vs_phieta_rep6.html
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'rep6 A/B FAST built and SOTA updated'

rep6-ab-full:
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py \
	  --full --float64 --psf-sigma 1.0 1.5 2.0 \
	  --hipass 4-8,8-16 --errfloor 0.03,3,7 --k 2 --rng 42 --s 0.4 0.6 1.0 \
	  --workers-auto
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py \
	  --full --float64 --psf-sigma 1.0 1.5 2.0 \
	  --hipass 4-8,8-16 --errfloor 0.03,3,7 --k 2 --rng 42 \
	  --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2
	  --workers-auto
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/reports/build_ws_vs_phieta_rep6.py \
	  --ws-json data/results/rep6_ws_full.json \
	  --if-json data/results/rep6_phieta_full.json \
	  --fair-json data/results/ws_vs_phieta_fair_best.json \
	  --out server/public/reports/ws_vs_phieta_rep6.html
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'rep6 A/B FULL built and SOTA updated'

.PHONY: info-params
info-params:
	PYTHONPATH=. ./.venv/bin/python scripts/info/save_params_info.py --kappa 1.0 --beta 0.3 --eta-model small_k_quadratic --D 0.0 --tau 1.0
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'saved params_info.json and rebuilt SOTA'

# ===== Early-Universe (Late-FDB) =====
.PHONY: eu-figs eu-all

eu-figs:
	PYTHONPATH=. ./.venv/bin/python scripts/plot_early_universe.py

eu-all: eu-figs
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py

.PHONY: early-fdb
early-fdb: eu-all
 	@echo 'alias: early-fdb -> eu-all'

.PHONY: eu-class
eu-class:
	PYTHONPATH=. ./.venv/bin/python scripts/eu/class_validate.py

# ===== Bullet Cluster (FDB thin-lens) =====
.PHONY: bullet-prep bullet-sigma bullet-fdb bullet-fit-train bullet-apply-holdout bullet-metrics bullet-all

bullet-prep:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/prep/reproject_all.py

.PHONY: bullet-fetch-kappa
bullet-fetch-kappa:
	@[ -n "$(URL)" ] || { echo 'Usage: make bullet-fetch-kappa URL=...'; exit 1; } \
	; PYTHONPATH=. ./.venv/bin/python scripts/cluster/prep/fetch_kappa.py "$(URL)"

.PHONY: bullet-reconstruct-ltm
bullet-reconstruct-ltm:
	@[ -n "$(URL)" ] || { echo 'Usage: make bullet-reconstruct-ltm URL=...'; exit 1; } \
	; PYTHONPATH=. ./.venv/bin/python scripts/cluster/reconstruct/ltm_from_optical.py "$(URL)"

bullet-sigma:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/maps/make_sigma_e.py

bullet-fdb:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/fdb/make_S_W.py || true; \
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/fdb/kappa_fdb.py || true

bullet-fit-train:
	# refine α,β,C by grid-search against observed kappa on matched grid
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/prep/regrid_to_kappa.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/gr/kappa_baryon.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/fit/grid_search_abc.py || true

bullet-apply-holdout:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/fit/apply_holdout.py || true

bullet-metrics:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/eval/metrics.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/controls/control_tests.py || true

bullet-all:
	$(MAKE) bullet-prep; \
	$(MAKE) bullet-sigma; \
	$(MAKE) bullet-fit-train; \
	$(MAKE) bullet-apply-holdout; \
	$(MAKE) bullet-metrics; \
	echo 'bullet cluster pipeline done'

# ===== Wayback κ fetch (generic + presets) =====
.PHONY: fetch-abell-kappa-wayback fetch-cl0024-kappa-wayback fetch-kappa-wayback

fetch-abell-kappa-wayback:
	bash scripts/fetch/fetch_kappa_wayback.sh NAME=Abell1689 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_data_catalog.py

fetch-cl0024-kappa-wayback:
	bash scripts/fetch/fetch_kappa_wayback.sh NAME=CL0024 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_data_catalog.py

# Custom seeds/pattern example:
#   make fetch-kappa-wayback NAME=Abell1689 SEEDS="http://foo/a1689/ http://bar/" PATTERN='(a1689).*(kappa).*\.(fits|fit)$'
fetch-kappa-wayback:
	@[ -n "$(NAME)" ] || { echo 'usage: make fetch-kappa-wayback NAME=<Cluster> [SEEDS=...] [PATTERN=...]'; exit 1; }
	bash scripts/fetch/fetch_kappa_wayback.sh NAME=$(NAME) ${SEEDS:+SEEDS="$(SEEDS)"} ${PATTERN:+PATTERN='$(PATTERN)'} || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_data_catalog.py

# ===== KS reconstruction fallback =====
.PHONY: reconstruct-ks
reconstruct-ks:
	@[ -n "$(NAME)" ] && [ -n "$(SHEAR)" ] || { echo 'usage: make reconstruct-ks NAME=<Cluster> SHEAR=<path-to-shear.dat>'; exit 1; }
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/reconstruct/kaiser_squires.py --name "$(NAME)" --shear "$(SHEAR)" --size ${SIZE:-256}
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_data_catalog.py

# ===== Controls (Negative-control batteries) =====
.PHONY: controls ctrl-tests
controls ctrl-tests:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_control_tests.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_halpha_control_boxplot.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'controls regenerated and SOTA rebuilt'

# ===== Phi·eta fair comparison & sweeps =====
.PHONY: rep6-phieta-fair phieta-profile
rep6-phieta-fair:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/compare_ws_vs_phieta.py --names NGC3198,NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/sweep_phieta_fair.py --names NGC3198,NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'Phi·eta fair comparison + sweep done and SOTA rebuilt'

.PHONY: ab-compare
ab-compare: rep6-phieta-fair
	@echo 'A/B（界面Σ vs Φ×η）フェア比較を再生成しました'

# ===== Bench (確定図: 外縁傾き・Hα/ω_cut・相関) =====
.PHONY: bench-ngc3198 bench-ngc2403

bench-ngc3198:
	PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/run_ngc3198_fullbench.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_outer_slope_stability.py --name NGC3198 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_omega_cut_contours.py --name NGC3198 --L-pc 100 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/angle_align_omega_cut_vs_afdb.py --name NGC3198 --L-pc 100 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/correlate_omega_cut_vs_residual.py --name NGC3198 --L-pc 100 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_env_toggle.py --name NGC3198 --L-pc 100 --alpha 1.0 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'bench-ngc3198 done'

bench-ngc2403:
	PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/run_ngc2403_fullbench.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_outer_slope_stability.py --name NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_omega_cut_contours.py --name NGC2403 --L-pc 100 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/angle_align_omega_cut_vs_afdb.py --name NGC2403 --L-pc 100 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/correlate_omega_cut_vs_residual.py --name NGC2403 --L-pc 100 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_env_toggle.py --name NGC2403 --L-pc 100 --alpha 1.0 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'bench-ngc2403 done'

# ===== Υ★–κ–C combined 90%CL =====
.PHONY: ykC-combined
ykC-combined:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/fit_kappa_C.py --names NGC3198,NGC2403 --prior phase --prior-strength 0.2 --beta 0.3 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/overlay_solar_bound_kappaC.py --file data/results/kappaC_fit.json --amax 1e-12 --Kc 1.0 --Kif 0.0 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_mu_kappa_C_combined.py --names NGC3198,NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'Υ★–κ–C 90%CL combined pages built'

# ===== KPI bundles =====
.PHONY: kpi-ab kpi-controls kpi-ykc kpi-bullet kpi-sprint

# KPI‑1: A/B 公平比較（高解像）+ J_Iビジュアル
kpi-ab:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/sweep_phieta_fair.py --names NGC3198,NGC2403 --max-size 320 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_JI_vector_panel.py --name NGC3198 --beta 0.3 --s 0.5 --sgk 0.6 --max-size 192 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'KPI‑1 (A/B) refreshed'

# KPI‑2: 対照検証の拡張（n≥50）
kpi-controls:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_control_tests.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_halpha_control_boxplot.py --n-rotate 50 --n-shift 50 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'KPI‑2 (controls) refreshed'

# KPI‑3: Υ★–κ–C 90%CL（数表付き）
kpi-ykc: ykC-combined

# KPI‑4: バレット（ホールドアウト・ダッシュボード再生成）
kpi-bullet:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/validate_bullet_holdout.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
	@echo 'KPI‑4 (Bullet holdout) refreshed'

# All KPI bundle
kpi-sprint: kpi-ab kpi-controls kpi-ykc kpi-bullet
	$(MAKE) notify-done-site

.PHONY: gate-kpi
gate-kpi:
	PYTHONPATH=. ./.venv/bin/python scripts/jobs/update_gate_kpi.py --pretty

.PHONY: nbody-kpi
nbody-kpi:
	PYTHONPATH=. ./.venv/bin/python scripts/jobs/update_nbody_kpi.py --pretty

.PHONY: holdout-standard
holdout-standard:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
		--holdout AbellS1063 --beta-sweep 0.6 --fast --downsample 1 \
		--sigma-psf 1.2 --sigma-highpass 6 --se-transform none \
		--weight-powers 0.0 --perm-n 10 --perm-min 10 --perm-max 10 \
		--perm-earlystop --band 8-16 --block-pix 6
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
		--holdout AbellS1063 --beta-sweep 0.6 \
		--sigma-psf 1.2 --sigma-highpass 6 --se-transform none \
		--weight-powers 0.0 --perm-n 10 --perm-min 10 --perm-max 10 \
		--perm-earlystop --band 8-16 --block-pix 6
	@echo 'AbellS1063 FAST/FULL (band=8-16, block_pix=6) refreshed for preproc_stamp検証'

.PHONY: kpi-weekly
kpi-weekly: gate-kpi nbody-kpi
	$(MAKE) notify-done

phieta-profile:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/profile_likelihood_mu_kappa.py --names NGC3198,NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'Profile-likelihood plots generated and SOTA rebuilt'

.PHONY: phieta-bg phieta-watch phieta-cancel
phieta-bg:
	bash scripts/phieta/run_phieta_bg.sh ${NAMES:+NAMES=$(NAMES)}

phieta-watch:
	bash scripts/phieta/watch_phieta.sh

phieta-cancel:
	bash scripts/phieta/cancel_phieta.sh

.PHONY: phieta-chunks phieta-chunks-watch
phieta-chunks:
	bash scripts/phieta/run_phieta_chunks.sh ${NAMES:+NAMES=$(NAMES)} ${BETAS:+BETAS=$(BETAS)}

phieta-chunks-watch:
	bash scripts/phieta/watch_phieta_chunks.sh

.PHONY: fdb-volume-watch
fdb-volume-watch:
	PYTHONPATH=. ./.venv/bin/python scripts/fdb_volume/watch_jobs.py ${LOG_DIR:+--log-dir $(LOG_DIR)} ${INTERVAL:+--interval $(INTERVAL)}

.PHONY: phieta-hits
phieta-hits:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/analyze_phieta_trials.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'Phi·eta hits summarized and SOTA rebuilt'

docs:
	PYTHONPATH=. $(PY) scripts/update_sota_lastmod.py
	bash scripts/sync_figs_to_docs.sh

site:
	mkdocs build --strict

serve:
	bash scripts/serve_site.sh 8000

publish-site:
	bash scripts/update_and_build_site.sh
	bash scripts/capture_env_logs.sh || true

# ==== Web server (TLS) ====
.PHONY: web-restart web-deploy

# 再起動のみ（server/public を配信; 動的SOTAは /state_of_the_art/）
web-restart:
	USE_TLS=0 bash scripts/start_web.sh

# 軽量デプロイ: SOTA静的の再生成 + 再起動
web-deploy:
	PYTHONPATH=. $(PY) scripts/build_state_of_the_art.py
	bash scripts/capture_env_logs.sh || true
	USE_TLS=0 bash scripts/start_web.sh

.PHONY: talker-restart talker-stop
talker-restart:
	bash scripts/start_talker.sh

talker-stop:
	@if [ -f server/talker.pid ]; then kill `cat server/talker.pid` 2>/dev/null || true; fi

.PHONY: capture-env
capture-env:
	bash scripts/capture_env_logs.sh

# ===== A-4 autopilot (watchers) =====
.PHONY: autopilot-a4
autopilot-a4:
	@# Watch FAST snapshots and dispatch FULL under Gate policy
	PYTHONPATH=. ./.venv/bin/python scripts/jobs/watch_gate_and_dispatch.py --holdouts AbellS1063,MACSJ0416 --interval 600 --once || true
	scripts/jobs/dispatch_bg.sh -n watch_gate_and_dispatch --scope -- \
	  "PYTHONPATH=. ./.venv/bin/python scripts/jobs/watch_gate_and_dispatch.py --holdouts AbellS1063,MACSJ0416 --interval 600" || true
	@# Ensure a continuous supply of FAST exploration jobs (one per holdout)
	@# Primer (one-off) then background watchers
	bash scripts/jobs/watch_fast_supply.sh --once AbellS1063 1 || true
	bash scripts/jobs/watch_fast_supply.sh --once MACSJ0416 1 || true
	scripts/jobs/dispatch_bg.sh -n watch_fast_supply_AbellS1063 --scope -- \
	  "bash scripts/jobs/watch_fast_supply.sh AbellS1063 300" || true
	scripts/jobs/dispatch_bg.sh -n watch_fast_supply_MACSJ0416 --scope -- \
	  "bash scripts/jobs/watch_fast_supply.sh MACSJ0416 300" || true
	@# Ensure summary watchers for both holdouts are running
	scripts/jobs/dispatch_bg.sh -n watch_collect_a4_AbellS1063 --scope -- \
	  "bash scripts/jobs/watch_collect_a4.sh AbellS1063 60" || true
	scripts/jobs/dispatch_bg.sh -n watch_collect_a4_MACSJ0416 --scope -- \
	  "bash scripts/jobs/watch_collect_a4.sh MACSJ0416 60" || true
	@echo 'A-4 autopilot watchers started'

# ===== WL strict (official vector + covariance) BG runner =====
.PHONY: wl-strict-bg
wl-strict-bg:
	@echo 'Dispatching WL strict (official vector + covariance) as background job'
	scripts/jobs/dispatch_bg.sh -n wl_strict_official --scope -- \
	  "set -e; \
	  export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc; \
	  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_wl_kids450_strict.py --theta-plus-min 4 --theta-minus-min 8.6 --theta-max 72 --m-bias 0 --ia-type NLA --ia-amp 0; \
	  PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py; \
	  stamp=\$(date +%Y-%m-%d_%H%M); \
	  cat > memo/run_\${stamp}_wl_strict_official_bg.md <<'MD'\n# WL 2PCF（KiDS-450）厳密（公式ベクトル＋共分散）BG実行\n\n## 結果サマリ\n- 公式130×130共分散と連結ベクトルにθカット（xip≤72′, xim≥8.6′）を適用し、k=0でΔAICcを評価。\n- SOTAへ反映。\n\n## 生成物\n- server/public/state_of_the_art/wl_2pcf_tomo_strict.html\n- server/public/state_of_the_art/index.html\n\n## 次アクション\n- m/IA（NLA/TATT）設定の反映・最終化。\nMD\n; \
	  make notify-done-site"

.PHONY: wl-mia-grid
wl-mia-grid:
	scripts/jobs/dispatch_bg.sh -n wl_mia_grid --scope -- \
	  "bash scripts/jobs/run_wl_mia_grid.sh"

paper-sota:
	bash scripts/sync_figs_to_paper.sh
e2e:
	set -euo pipefail; \
	[ -f .env ] && set -a && . ./.env && set +a || true; \
	PYTHONPATH=. ./.venv/bin/python scripts/e2e_site_check.py; \
	echo 'E2E done.'
## === Convenience run targets (scripts) ===
.PHONY: sota-figs build-sota cv-shared bench-ngc3198 demo-two-layer

sota-figs:
	PYTHONPATH=. ./.venv/bin/python scripts/plot_sota_figs.py || true

build-sota:
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py

# Run site audits (consistency/links/http) and rebuild SOTA to reflect badges
BASE ?=
site-audit:
	set -euo pipefail; \
	[ -n "$(BASE)" ] && export BASE=$(BASE) || true; \
	PYTHONPATH=. ./.venv/bin/python scripts/qa/run_site_audit.py || true; \
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py; \
	echo 'site audit completed and SOTA rebuilt'

.PHONY: site-audit-ci
site-audit-ci:
	set -euo pipefail; \
	[ -n "$(BASE)" ] && export BASE=$(BASE) || true; \
	PYTHONPATH=. ./.venv/bin/python scripts/qa/run_site_audit.py; \
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py; \
	echo 'site audit (CI) passed and SOTA rebuilt'

cv-shared:
	PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py \
		--names-file data/sparc/sets/clean_for_fit.txt --out-prefix cv_shared_summary \
		--robust huber --fixed-mu-eps 1 --fixed-mu-k0 0.2 --fixed-mu-m 2 --fixed-gas-scale 1.33

# [dedupe] Removed duplicate minimal recipes for bench targets (now defined above)

demo-two-layer:
	PYTHONPATH=. ./.venv/bin/python scripts/demos/two_layer_demo.py

# [dedupe] Removed older H-alpha ingestion recipes in favor of improved versions later in file

.PHONY: vres-ngc3198
vres-ngc3198:
	@echo "Usage: make vres-ngc3198 IN=path/to/velocity.fits [SIGMA=1.0]"; \
	if [ -n "$(IN)" ]; then \
	  mkdir -p data/vel/NGC3198; cp "$(IN)" data/vel/NGC3198/velocity.fits; \
	  PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_ngc3198_vfield_residual.py ${SIGMA:+--sigma-pix $(SIGMA)}; \
	else \
	  echo "IN を指定してください" >&2; exit 1; \
	fi

.PHONY: vres-ngc2403
vres-ngc2403:
	@echo "Usage: make vres-ngc2403 IN=path/to/velocity.fits [SIGMA=1.0]"; \
	if [ -n "$(IN)" ]; then \
	  mkdir -p data/vel/NGC2403; cp "$(IN)" data/vel/NGC2403/velocity.fits; \
	  PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_ngc2403_vfield_residual.py ${SIGMA:+--sigma-pix $(SIGMA)}; \
	else \
	  echo "IN を指定してください" >&2; exit 1; \
	fi

.PHONY: nc-components
nc-components:
	PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_noncircular_diagnostics.py --name NGC3198 || true
	PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_noncircular_diagnostics.py --name NGC2403 || true

.PHONY: bench-both-bg bench-watch
bench-both-bg:
	bash scripts/benches/run_benches_bg.sh

bench-watch:
	bash scripts/benches/watch_benches.sh

.PHONY: ne-null sensitivity
ne-null:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_ne_perturbation_report.py

sensitivity:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_sensitivity_radar.py

.PHONY: omega-cut
omega-cut:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_omega_cut_contours.py --name NGC3198 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_omega_cut_contours.py --name NGC2403 || true

.PHONY: wcut-corr
wcut-corr:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/correlate_omega_cut_vs_residual.py --name NGC3198 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/correlate_omega_cut_vs_residual.py --name NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'omega_cut correlations computed and SOTA rebuilt'

.PHONY: angle-align
angle-align:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/angle_align_omega_cut_vs_afdb.py --name NGC3198 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/angle_align_omega_cut_vs_afdb.py --name NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'angle alignment computed and SOTA rebuilt'

.PHONY: kappaC-fit
kappaC-fit:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/fit_kappa_C.py --names NGC3198,NGC2403 || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'kappa/C fit done and SOTA rebuilt'

.PHONY: solar-bound
solar-bound:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/overlay_solar_bound_kappaC.py --file data/results/kappaC_fit.json --amax 1e-12 --Kc 1.0 --Kif 0.0 || true

.PHONY: bullet-holdout
bullet-holdout:
	@:
	BULLET_PERM_N=$${BULLET_PERM_N:-1024} PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/validate_bullet_holdout.py || true

# ===== Lenstool κ build from tarballs =====
.PHONY: kappa-from-tarballs kappa-a1689 kappa-cl0024
kappa-from-tarballs:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/prep/build_kappa_from_tarballs.py || true

kappa-a1689:
	@[ -f tmp/a1689.tar.gz ] || (echo 'missing tmp/a1689.tar.gz'; false)
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/prep/build_kappa_from_tarballs.py --a1689 tmp/a1689.tar.gz --cl0024 /nonexistent || true

kappa-cl0024:
	@[ -f tmp/cl0024.tar.gz ] || (echo 'missing tmp/cl0024.tar.gz'; false)
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/prep/build_kappa_from_tarballs.py --a1689 /nonexistent --cl0024 tmp/cl0024.tar.gz || true

.PHONY: train-freeze-shared
train-freeze-shared:
	PYTHONPATH=. ./.venv/bin/python scripts/cluster/fit/train_shared_params.py || true

.PHONY: fetch-inputs
fetch-inputs:
	bash scripts/fetch/fetch_inputs.sh

.PHONY: fetch-irac1-3198
fetch-irac1-3198:
	NAME=NGC3198 bash scripts/fetch/fetch_irsa_irac1.sh || true

.PHONY: fetch-irac1-2403
fetch-irac1-2403:
	NAME=NGC2403 bash scripts/fetch/fetch_irsa_irac1.sh || true

.PHONY: fetch-bullet-hst
fetch-bullet-hst:
	bash scripts/fetch/fetch_hst_bullet.sh || true

.PHONY: fetch-bullet
fetch-bullet:
	bash scripts/fetch/fetch_bullet.sh

.PHONY: fetch-abell
fetch-abell:
	@[ -n "$(OBSIDS)" ] || (echo 'usage: make fetch-abell OBSIDS="<space-separated obsids>"' && false)
	NAME=Abell1689 OBSIDS="$(OBSIDS)" bash scripts/fetch/fetch_cluster_cxo.sh

.PHONY: fetch-cl0024
fetch-cl0024:
	@[ -n "$(OBSIDS)" ] || (echo 'usage: make fetch-cl0024 OBSIDS="<space-separated obsids>"' && false)
	NAME=CL0024 OBSIDS="$(OBSIDS)" bash scripts/fetch/fetch_cluster_cxo.sh

.PHONY: ha-ngc3198
ha-ngc3198:
	@[ -f "$(IN)" ] || (echo 'usage: make ha-ngc3198 IN=path/to/ngc3198_HA_SUB_dr4.fits [NII=0.3] [EBV=0.04] [KHA=2.53]' && false)
	PYTHONPATH=. ./.venv/bin/python scripts/halpha/ingest_halpha.py --in "$(IN)" --name NGC3198 --nii-ratio $(or $(NII),0.3) --ebv $(or $(EBV),0.04) --k-ha $(or $(KHA),2.53)
	PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_ngc3198_ha_overlay.py || true

.PHONY: ha-ngc2403
ha-ngc2403:
	@[ -f "$(IN_HA)" ] && [ -f "$(IN_R)" ] || (echo 'usage: make ha-ngc2403 IN_HA=.../ngc2403_HA.fits IN_R=.../ngc2403_R.fits [NII=0.3] [EBV=0.04] [KHA=2.53]' && false)
	PYTHONPATH=. ./.venv/bin/python scripts/halpha/make_ha_sub_from_continuum.py --ha "$(IN_HA)" --cont "$(IN_R)" --out data/sings/ngc2403_HA_SUB.fits || true
	PYTHONPATH=. ./.venv/bin/python scripts/halpha/ingest_halpha.py --in data/sings/ngc2403_HA_SUB.fits --name NGC2403 --nii-ratio $(or $(NII),0.3) --ebv $(or $(EBV),0.04) --k-ha $(or $(KHA),2.53)
	PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_ngc2403_ha_overlay.py || true

.PHONY: sota-refresh
sota-refresh:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_progress_dashboard.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true

# ===== rep6 A/B (W·S vs Φ·η) =====
.PHONY: rep6-fast rep6-full rep6-quick
rep6-fast:
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py --fast --downsample 2 --float32 --psf-sigma 1.0 1.5 --hipass 8-16 --errfloor 0.03,3,7 --k 2 --rng 42
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py --fast --downsample 2 --float32 --psf-sigma 1.0 1.5 --hipass 8-16 --errfloor 0.03,3,7 --k 2 --rng 42 --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/reports/build_ws_vs_phieta_rep6.py --ws-json data/results/rep6_ws_fast.json --if-json data/results/rep6_phieta_fast.json
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	@echo 'rep6-fast rebuilt'

rep6-full:
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py --full --float64 --psf-sigma 1.0 1.5 2.0 --hipass 4-8,8-16 --errfloor 0.03,3,7 --k 2 --rng 42
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py --full --float64 --psf-sigma 1.0 1.5 2.0 --hipass 4-8,8-16 --errfloor 0.03,3,7 --k 2 --rng 42 --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2
	$(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/reports/build_ws_vs_phieta_rep6.py --ws-json data/results/rep6_ws_full.json --if-json data/results/rep6_phieta_full.json
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	@echo 'rep6-full rebuilt'

rep6-quick: rep6-fast
	$(MAKE) notify-done-site MSG="rep6: A/B(WS vs Φ·η) 再計算(FAST)完了" TITLE="rep6 FAST"

# ===== Background-dispatched variants (isolated from Codex/tmux) =====
.PHONY: rep6-ab-fast-bg rep6-ab-full-bg jobs-run jobs-status jobs-cancel

CMD_REP6_AB_FAST = set -euo pipefail; \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py \
    --fast --downsample 2 --float32 --psf-sigma 1.0 1.5 --hipass 8-16 --errfloor 0.03,3,7 --k 2 --rng 42 && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py \
    --fast --downsample 2 --float32 --psf-sigma 1.0 1.5 --hipass 8-16 --errfloor 0.03,3,7 --k 2 --rng 42 --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2 && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/reports/build_ws_vs_phieta_rep6.py \
    --ws-json data/results/rep6_ws_fast.json --if-json data/results/rep6_phieta_fast.json

CMD_REP6_AB_FULL = set -euo pipefail; \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_ws.py \
    --full --float64 --psf-sigma 1.0 1.5 2.0 --hipass 4-8,8-16 --errfloor 0.03,3,7 --k 2 --rng 42 && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py \
    --full --float64 --psf-sigma 1.0 1.5 2.0 --hipass 4-8,8-16 --errfloor 0.03,3,7 --k 2 --rng 42 --beta 0.0 0.3 --s 0.4 0.6 1.0 --sigk 0.5 0.8 1.2 && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/reports/build_ws_vs_phieta_rep6.py \
    --ws-json data/results/rep6_ws_full.json --if-json data/results/rep6_phieta_full.json

rep6-ab-fast-bg:
	bash scripts/jobs/dispatch_bg.sh -n rep6_ab_fast -- "$(CMD_REP6_AB_FAST)" || true

rep6-ab-full-bg:
	bash scripts/jobs/dispatch_bg.sh -n rep6_ab_full -- "$(CMD_REP6_AB_FULL)" || true

jobs-run: ## NAME=foo CMD='echo hello'
	[ -n "$(NAME)" ] || { echo 'NAME is required' >&2; exit 1; }
	[ -n "$(CMD)" ]  || { echo 'CMD is required'  >&2; exit 1; }
	bash scripts/jobs/dispatch_bg.sh -n "$(NAME)" -- "$(CMD)"

jobs-status:
	PYTHONPATH=. ./.venv/bin/python scripts/jobs/status.py || true

jobs-cancel: ## NAME=foo
	[ -n "$(NAME)" ] || { echo 'NAME is required' >&2; exit 1; }
	bash scripts/jobs/cancel_job.sh -n "$(NAME)"

# Background progress pipeline (requires RATE and optional NOTE)
.PHONY: progress-bg
CMD_PROGRESS = set -euo pipefail; \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/update_progress.py --rate $(RATE) --note "$(NOTE)" && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/clean_for_fit.txt --out-prefix cv_shared_summary && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/lsb_noBL.txt --out-prefix cv_shared_summary_lsb_noBL && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py --names-file data/sparc/sets/hsb_noBL.txt --out-prefix cv_shared_summary_hsb_noBL && \
  $(MEMSAFE_ENV) PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py

progress-bg:
	[ -n "$(RATE)" ] || { echo 'RATE を0..100で指定してください' >&2; exit 1; }
	bash scripts/jobs/dispatch_bg.sh -n progress -- "$(CMD_PROGRESS)"

.PHONY: data-catalog
data-catalog:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_data_catalog.py

# ===== Progress dashboard =====
.PHONY: progress-report
progress-report:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_progress_dashboard.py
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	@echo 'progress dashboard generated and SOTA rebuilt'
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	echo 'Solar-system bound overlays generated and SOTA rebuilt'

# ===== Lightweight sanity cards (ΔAICc≈0) =====
.PHONY: wl-light cmb-light kosmo-light
wl-light:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_wl_2pcf_light.py
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	@echo 'WL 2PCF light card generated and SOTA rebuilt'

cmb-light:
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_cmb_peak_light.py
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py
	@echo 'CMB peaks light card generated and SOTA rebuilt'

kosmo-light: wl-light cmb-light
	@echo 'Cosmo “does-not-break” sanity cards updated'
.PHONY: audit
audit:
	PYTHONPATH=. ./.venv/bin/python scripts/qa/run_site_audit.py || true
.PHONY: data-get-ngc3198 data-get-ngc2403 fetch-halogas-ngc3198 fetch-halpha-ngc3198 fetch-things-ngc2403

fetch-halogas-ngc3198:
	bash scripts/fetch_halogas_ngc3198.sh

fetch-halpha-ngc3198:
	@echo "Usage: make fetch-halpha-ngc3198 URL=https://.../HA_SUB.fits"; \
	if [ -n "$(URL)" ]; then \
	  GAL=NGC3198 URL="$(URL)" bash scripts/fetch_halpha_irsa.sh; \
	else \
	  echo "URL を指定してください (IRSAのHA_SUB直リンク)" >&2; exit 1; \
	fi

fetch-things-ngc2403:
	@echo "注意: THINGSの公式配布はサイト改版でURLが変わる場合があります。"; \
	if [ -n "$(URL)" ]; then \
	  mkdir -p data/things/NGC2403; \
	  curl -fL --retry 3 "$(URL)" -o data/things/NGC2403/NGC2403_THINGS_cube.fits; \
	  echo "保存: data/things/NGC2403/NGC2403_THINGS_cube.fits"; \
	  echo "moment-1 を生成して velocity.fits へ配置します..."; \
	  python3 - <<PY; \
from spectral_cube import SpectralCube; from astropy import units as u; from astropy.io import fits; import os; \
cube = SpectralCube.read('data/things/NGC2403/NGC2403_THINGS_cube.fits'); vc = cube.with_spectral_unit(u.km/u.s); \
mom1 = vc.moment(order=1); hdr = mom1.header; hdr['BUNIT']='km/s'; os.makedirs('data/vel/NGC2403', exist_ok=True); \
fits.writeto('data/vel/NGC2403/velocity.fits', mom1.value.astype('f4'), hdr, overwrite=True); print('wrote data/vel/NGC2403/velocity.fits') \
PY
	else \
	  echo "URL= で THINGS データキューブの直リンクを指定してください" >&2; exit 1; \
	fi

data-get-ngc3198: fetch-halogas-ngc3198 fetch-halpha-ngc3198

data-get-ngc2403: fetch-things-ngc2403
# ===== Paper (single-source HTML/PDF) =====
.PHONY: paper-vars paper-html paper-pdf arxiv-pack paper-all

paper-vars:
	PYTHONPATH=. ./.venv/bin/python scripts/paper/generate_vars.py
	PYTHONPATH=. ./.venv/bin/python scripts/paper/collect_figs.py
	PYTHONPATH=. ./.venv/bin/python scripts/paper/generate_tex.py

paper-html: paper-vars
	@if ! command -v quarto >/dev/null 2>&1 && ! command -v pandoc >/dev/null 2>&1; then \
	  echo 'pandoc/quarto が見つかりません。ローカル環境にインストールしてください。' >&2; \
	  echo 'Quarto: https://quarto.org/  Pandoc: https://pandoc.org/' >&2; \
	  exit 0; \
	fi; \
	if command -v quarto >/dev/null 2>&1; then \
	  (cd paper && quarto render --to html); \
	else \
	  echo 'quarto未検出: pandocで簡易HTMLを生成します'; \
	  pandoc -s -t html5 -V mathjax --metadata-file=paper/_variables.yml -o paper/paper.html paper/paper.qmd; \
	fi

paper-pdf: paper-vars
	@if ! command -v quarto >/dev/null 2>&1 && ! command -v pandoc >/dev/null 2>&1; then \
	  echo 'pandoc/quarto が見つかりません。PDF生成をスキップします。' >&2; exit 0; \
	fi; \
	if command -v quarto >/dev/null 2>&1; then \
	  (cd paper && quarto render --to pdf); \
	else \
	  echo 'quarto未検出: pandocでPDFを試行します（LaTeX環境が必要）'; \
	  pandoc -s -V documentclass=revtex4-2 --pdf-engine=xelatex \
	    --metadata-file=paper/_variables.yml -o paper/paper.pdf paper/paper.qmd || true; \
	fi

arxiv-pack: paper-pdf
	@mkdir -p paper/dist; \
	shopt -s nullglob; \
	set -e; \
	files=(paper/*.tex paper/*.qmd paper/*.html paper/*.pdf paper/*.bbl paper/*.bib paper/preamble.tex paper/_variables.yml paper/quarto.yml); \
	figs=(paper/figures/*.{pdf,png,svg}); \
	zip -r paper/dist/arxiv-src.zip $${files[@]} $${figs[@]} >/dev/null 2>&1 || true; \
	echo 'packed: paper/dist/arxiv-src.zip'

paper-all: paper-html paper-pdf arxiv-pack

start:
	@if command -v setsid >/dev/null 2>&1; then \
	  setsid -w codex --search --dangerously-bypass-approvals-and-sandbox; \
	else \
	  codex --search --dangerously-bypass-approvals-and-sandbox; \
	fi

continue:
	@if command -v setsid >/dev/null 2>&1; then \
	  setsid -w codex resume --search --dangerously-bypass-approvals-and-sandbox --last; \
	else \
	  codex resume --search --dangerously-bypass-approvals-and-sandbox --last; \
	fi

resume:
	  codex resume --search --dangerously-bypass-approvals-and-sandbox $(ID)


.PHONY: ciao-bullet
ciao-bullet:
	bash scripts/cluster/cxo/build_sigma_wcut_ciao.sh Bullet 0.5:2.0 || true
	PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py || true
	PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true

.PHONY: fetch-bullet-cxo
fetch-bullet-cxo:
	bash scripts/cluster/cxo/fetch_bullet_obsids.sh || true
