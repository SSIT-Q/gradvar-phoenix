# Trial: properties history of finished jobs (20261111T041956Z)

Backend `ibm_phoenix`; ids files: `data/runs/2026-11-10/paper1_replication_01_16384_job_ids.json`, `data/runs/2026-11-10/paper1_section3c_blockC_job_ids.json`; margin after `finished`: 6.0 h; no instant later than 2026-11-11T04:19:56.328837Z was asked for. No job was submitted, `job.result()` was not called, no measured value is in this file or in the JSON beside it (`trial_properties_history_20261111T041956Z.json`).

**The run completed.**

Verdicts: AGREE 27, DISAGREE 0, INFO 19, NOT CHECKED 3, REFUSED 0.

## Table

| job | check | verdict | detail |
|---|---|---|---|
| dbpfnr0qtr0c738ebeng (L0) | job.properties() equals backend.properties(datetime=running) | **AGREE** | both: IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfnr0qtr0c738ebeng (L0) | set at running against the committed record | **AGREE** | IBM update 2026-11-10T09:07:11Z, the latest committed update at or before running |
| dbpfnr0qtr0c738ebeng (L0) | walk-back returns every intermediate set | **AGREE** | 6 sets from 2026-11-10T09:07:11Z to 2026-11-10T16:34:05Z: 2026-11-10T09:07:11Z, 2026-11-10T11:20:04Z, 2026-11-10T11:35:39Z, 2026-11-10T13:14:38Z, 2026-11-10T13:37:31Z, 2026-11-10T16:34:05Z; every committed update in that span was returned (3) |
| dbpfnr0qtr0c738ebeng (L0) | updates the repository never committed | **INFO** | returned by the walk-back and absent from data/calibrations: 2026-11-10T11:20:04Z, 2026-11-10T13:14:38Z, 2026-11-10T16:34:05Z |
| dbpfnr0qtr0c738ebeng (L0) | first set after finished | **INFO** | IBM update 2026-11-10T13:14:38Z; the repository holds no update between finished and it |
| dbpfnr0qtr0c738ebeng (L0) | updates published between running and finished | **INFO** | 2026-11-10T11:20:04Z, 2026-11-10T11:35:39Z |
| dbpfnr0qtr0c738ebeng (L0) | backend.properties(datetime=created) equals the bundle's properties.json | **AGREE** | IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfnr0qtr0c738ebeng (L0) | job metadata carries execution spans | **INFO** | no field of job.metrics() names a span (fields: caller, circuits_execution_time_ns, qiskit_version, timestamps, usage). Spans inside the result object were not looked for: job.result() is never called. |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | job.properties() equals backend.properties(datetime=running) | **AGREE** | both: IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | set at running against the committed record | **AGREE** | IBM update 2026-11-10T09:07:11Z, the latest committed update at or before running |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | walk-back returns every intermediate set | **AGREE** | 6 sets from 2026-11-10T09:07:11Z to 2026-11-10T16:34:05Z: 2026-11-10T09:07:11Z, 2026-11-10T11:20:04Z, 2026-11-10T11:35:39Z, 2026-11-10T13:14:38Z, 2026-11-10T13:37:31Z, 2026-11-10T16:34:05Z; every committed update in that span was returned (3) |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | updates the repository never committed | **INFO** | returned by the walk-back and absent from data/calibrations: 2026-11-10T11:20:04Z, 2026-11-10T13:14:38Z, 2026-11-10T16:34:05Z |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | first set after finished | **AGREE** | IBM update 2026-11-10T11:35:39Z, the first committed update after finished (2026-11-10T11:21:02.733793Z) |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | updates published between running and finished | **INFO** | 2026-11-10T11:20:04Z |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | backend.properties(datetime=created) equals the bundle's properties.json | **AGREE** | IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfnrgqtr0c738ebeog (L0-probes-s16384) | job metadata carries execution spans | **INFO** | no field of job.metrics() names a span (fields: caller, circuits_execution_time_ns, qiskit_version, timestamps, usage). Spans inside the result object were not looked for: job.result() is never called. |
| dbpfom8ou4as73ctjes0 (L0) | job.properties() equals backend.properties(datetime=running) | **AGREE** | both: IBM update 2026-11-10T11:35:39Z, sha256 b944518f6451 |
| dbpfom8ou4as73ctjes0 (L0) | set at running against the committed record | **AGREE** | IBM update 2026-11-10T11:35:39Z, the latest committed update at or before running |
| dbpfom8ou4as73ctjes0 (L0) | walk-back returns every intermediate set | **AGREE** | 6 sets from 2026-11-10T09:07:11Z to 2026-11-10T16:34:05Z: 2026-11-10T09:07:11Z, 2026-11-10T11:20:04Z, 2026-11-10T11:35:39Z, 2026-11-10T13:14:38Z, 2026-11-10T13:37:31Z, 2026-11-10T16:34:05Z; every committed update in that span was returned (3) |
| dbpfom8ou4as73ctjes0 (L0) | updates the repository never committed | **INFO** | returned by the walk-back and absent from data/calibrations: 2026-11-10T11:20:04Z, 2026-11-10T13:14:38Z, 2026-11-10T16:34:05Z |
| dbpfom8ou4as73ctjes0 (L0) | first set after finished | **AGREE** | IBM update 2026-11-10T13:37:31Z, the first committed update after finished (2026-11-10T13:31:41.789031Z) |
| dbpfom8ou4as73ctjes0 (L0) | updates published between running and finished | **INFO** | 2026-11-10T13:14:38Z |
| dbpfom8ou4as73ctjes0 (L0) | backend.properties(datetime=created) equals the bundle's properties.json | **AGREE** | IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfom8ou4as73ctjes0 (L0) | job metadata carries execution spans | **INFO** | no field of job.metrics() names a span (fields: caller, circuits_execution_time_ns, qiskit_version, timestamps, usage). Spans inside the result object were not looked for: job.result() is never called. |
| dbpfon8qtr0c738ebgj0 (L0-c2) | job.properties() equals backend.properties(datetime=running) | **AGREE** | both: IBM update 2026-11-10T11:35:39Z, sha256 b944518f6451 |
| dbpfon8qtr0c738ebgj0 (L0-c2) | set at running against the committed record | **AGREE** | IBM update 2026-11-10T11:35:39Z, the latest committed update at or before running |
| dbpfon8qtr0c738ebgj0 (L0-c2) | walk-back returns every intermediate set | **AGREE** | 6 sets from 2026-11-10T09:07:11Z to 2026-11-10T16:34:05Z: 2026-11-10T09:07:11Z, 2026-11-10T11:20:04Z, 2026-11-10T11:35:39Z, 2026-11-10T13:14:38Z, 2026-11-10T13:37:31Z, 2026-11-10T16:34:05Z; every committed update in that span was returned (3) |
| dbpfon8qtr0c738ebgj0 (L0-c2) | updates the repository never committed | **INFO** | returned by the walk-back and absent from data/calibrations: 2026-11-10T11:20:04Z, 2026-11-10T13:14:38Z, 2026-11-10T16:34:05Z |
| dbpfon8qtr0c738ebgj0 (L0-c2) | first set after finished | **INFO** | IBM update 2026-11-10T13:14:38Z; the repository holds no update between finished and it |
| dbpfon8qtr0c738ebgj0 (L0-c2) | updates published between running and finished | **INFO** | none |
| dbpfon8qtr0c738ebgj0 (L0-c2) | backend.properties(datetime=created) equals the bundle's properties.json | **AGREE** | IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfon8qtr0c738ebgj0 (L0-c2) | job metadata carries execution spans | **INFO** | no field of job.metrics() names a span (fields: caller, circuits_execution_time_ns, qiskit_version, timestamps, usage). Spans inside the result object were not looked for: job.result() is never called. |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | job.properties() equals backend.properties(datetime=running) | **AGREE** | both: IBM update 2026-11-10T11:35:39Z, sha256 b944518f6451 |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | set at running against the committed record | **AGREE** | IBM update 2026-11-10T11:35:39Z, the latest committed update at or before running |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | walk-back returns every intermediate set | **AGREE** | 6 sets from 2026-11-10T09:07:11Z to 2026-11-10T16:34:05Z: 2026-11-10T09:07:11Z, 2026-11-10T11:20:04Z, 2026-11-10T11:35:39Z, 2026-11-10T13:14:38Z, 2026-11-10T13:37:31Z, 2026-11-10T16:34:05Z; every committed update in that span was returned (3) |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | updates the repository never committed | **INFO** | returned by the walk-back and absent from data/calibrations: 2026-11-10T11:20:04Z, 2026-11-10T13:14:38Z, 2026-11-10T16:34:05Z |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | first set after finished | **INFO** | IBM update 2026-11-10T13:14:38Z; the repository holds no update between finished and it |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | updates published between running and finished | **INFO** | none |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | backend.properties(datetime=created) equals the bundle's properties.json | **AGREE** | IBM update 2026-11-10T09:07:11Z, sha256 d43975dc9169 |
| dbpfontt7fqc7389bsu0 (L0-probes-s65536) | job metadata carries execution spans | **INFO** | no field of job.metrics() names a span (fields: caller, circuits_execution_time_ns, qiskit_version, timestamps, usage). Spans inside the result object were not looked for: job.result() is never called. |
| all | published set is immutable (2026-11-10T09:07:11Z) | **AGREE** | sha256 d43975dc9169 equals 5 committed file(s): ibm_phoenix_properties_2026-11-10T111132Z.json, ibm_phoenix_properties_2026-11-10T111320Z.json, ibm_phoenix_properties_20261110T101610Z.json.gz |
| all | published set is immutable (2026-11-10T11:20:04Z) | **NOT CHECKED** | the repository holds no file of this IBM update |
| all | published set is immutable (2026-11-10T11:35:39Z) | **AGREE** | sha256 b944518f6451 equals 1 committed file(s): ibm_phoenix_properties_2026-11-10T124546Z.json |
| all | published set is immutable (2026-11-10T13:14:38Z) | **NOT CHECKED** | the repository holds no file of this IBM update |
| all | published set is immutable (2026-11-10T13:37:31Z) | **AGREE** | sha256 ff258e53639b equals 1 committed file(s): ibm_phoenix_properties_2026-11-10T135646Z.json |
| all | published set is immutable (2026-11-10T16:34:05Z) | **NOT CHECKED** | the repository holds no file of this IBM update |
| all | one content per IBM update within this run | **AGREE** | 6 updates, each returned with one content by 26 calls |
| all | backend.properties accepts datetime | **AGREE** | 21 calls answered; no NotImplementedError |
| all | is datetime inclusive | **INFO** | asked for exactly 2026-11-10T16:34:05Z: the service returned the set of 2026-11-10T13:37:31Z (exclusive: strictly older than the instant asked) |

## Jobs

| job | tag | created | running | finished | job.properties() | at running | at created | first after finished | sets of the walk-back (newest first) |
|---|---|---|---|---|---|---|---|---|---|
| dbpfnr0qtr0c738ebeng | L0 | 2026-11-10T11:11:40.956832Z | 2026-11-10T11:12:05.243865Z | 2026-11-10T12:35:07.784468Z | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T13:14:38Z `6331a7c9c5b6` | 2026-11-10T16:34:05Z `60a212c41b76`; 2026-11-10T13:37:31Z `ff258e53639b`; 2026-11-10T13:14:38Z `6331a7c9c5b6`; 2026-11-10T11:35:39Z `b944518f6451`; 2026-11-10T11:20:04Z `c80d21378e55`; 2026-11-10T09:07:11Z `d43975dc9169` |
| dbpfnrgqtr0c738ebeog | L0-probes-s16384 | 2026-11-10T11:11:42.219926Z | 2026-11-10T11:12:33.691043Z | 2026-11-10T11:21:02.733793Z | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T16:34:05Z `60a212c41b76`; 2026-11-10T13:37:31Z `ff258e53639b`; 2026-11-10T13:14:38Z `6331a7c9c5b6`; 2026-11-10T11:35:39Z `b944518f6451`; 2026-11-10T11:20:04Z `c80d21378e55`; 2026-11-10T09:07:11Z `d43975dc9169` |
| dbpfom8ou4as73ctjes0 | L0 | 2026-11-10T11:13:29.583977Z | 2026-11-10T12:54:18.417644Z | 2026-11-10T13:31:41.789031Z | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T13:37:31Z `ff258e53639b` | 2026-11-10T16:34:05Z `60a212c41b76`; 2026-11-10T13:37:31Z `ff258e53639b`; 2026-11-10T13:14:38Z `6331a7c9c5b6`; 2026-11-10T11:35:39Z `b944518f6451`; 2026-11-10T11:20:04Z `c80d21378e55`; 2026-11-10T09:07:11Z `d43975dc9169` |
| dbpfon8qtr0c738ebgj0 | L0-c2 | 2026-11-10T11:13:34.870713Z | 2026-11-10T12:54:22.817673Z | 2026-11-10T13:10:40.143310Z | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T13:14:38Z `6331a7c9c5b6` | 2026-11-10T16:34:05Z `60a212c41b76`; 2026-11-10T13:37:31Z `ff258e53639b`; 2026-11-10T13:14:38Z `6331a7c9c5b6`; 2026-11-10T11:35:39Z `b944518f6451`; 2026-11-10T11:20:04Z `c80d21378e55`; 2026-11-10T09:07:11Z `d43975dc9169` |
| dbpfontt7fqc7389bsu0 | L0-probes-s65536 | 2026-11-10T11:13:35.793803Z | 2026-11-10T12:54:47.256563Z | 2026-11-10T13:08:16.181825Z | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T11:35:39Z `b944518f6451` | 2026-11-10T09:07:11Z `d43975dc9169` | 2026-11-10T13:14:38Z `6331a7c9c5b6` | 2026-11-10T16:34:05Z `60a212c41b76`; 2026-11-10T13:37:31Z `ff258e53639b`; 2026-11-10T13:14:38Z `6331a7c9c5b6`; 2026-11-10T11:35:39Z `b944518f6451`; 2026-11-10T11:20:04Z `c80d21378e55`; 2026-11-10T09:07:11Z `d43975dc9169` |

## Sets

| IBM update | sha256 of the canonical JSON | file | readout_error dates | init_error dates | gate_error:cz dates | gate_error:sx dates | T1 dates |
|---|---|---|---|---|---|---|---|
| 2026-11-10T09:07:11Z | `d43975dc91698c38258a1f1535900eef97826ab31c106d9ccdb0eb03100092cc` | `data/calibrations/trial_2026-11-10/ibm_phoenix_properties_update_20261110T090711Z_d43975dc9169.json` | 2026-11-09T04:54:44Z to 2026-11-09T04:54:47Z (4 distinct, n = 120) | 2026-08-25T15:23:25Z to 2026-11-10T08:44:38Z (41 distinct, n = 116) | 2026-10-29T10:53:46Z to 2026-11-10T09:09:27.162123Z (16 distinct, n = 436) | 2026-10-31T05:57:44Z to 2026-11-10T09:09:25Z (8 distinct, n = 120) | 2026-11-07T02:19:57Z to 2026-11-09T20:15:14Z (5 distinct, n = 119) |
| 2026-11-10T11:20:04Z | `c80d21378e55e82df0fc84efb4a6fb8bcd3b823e8f14b998c85b94889aaed931` | `data/calibrations/trial_2026-11-10/ibm_phoenix_properties_update_20261110T112004Z_c80d21378e55.json` | 2026-11-10T11:05:20Z to 2026-11-10T11:05:20Z (1 distinct, n = 120) | 2026-08-25T15:23:25Z to 2026-11-10T11:20:04Z (58 distinct, n = 116) | 2026-10-29T10:53:46Z to 2026-11-10T11:20:24.888342Z (16 distinct, n = 436) | 2026-10-31T05:57:44Z to 2026-11-10T11:20:23Z (8 distinct, n = 120) | 2026-11-07T02:19:57Z to 2026-11-09T20:15:14Z (5 distinct, n = 119) |
| 2026-11-10T11:35:39Z | `b944518f6451e1e2d359ae379ee63e90a0e92ea1b4dd938fdd7a5245dd4fcdc0` | `data/calibrations/trial_2026-11-10/ibm_phoenix_properties_update_20261110T113539Z_b944518f6451.json` | 2026-11-10T11:05:20Z to 2026-11-10T11:05:20Z (1 distinct, n = 120) | 2026-08-25T15:23:25Z to 2026-11-10T11:20:04Z (58 distinct, n = 116) | 2026-10-29T10:53:46Z to 2026-11-10T11:38:31.225232Z (16 distinct, n = 436) | 2026-10-31T05:57:44Z to 2026-11-10T11:38:29Z (8 distinct, n = 120) | 2026-11-07T02:19:57Z to 2026-11-09T20:15:14Z (5 distinct, n = 119) |
| 2026-11-10T13:14:38Z | `6331a7c9c5b67ebf2f6e72d51217ae129949132e2388534fe9250c9c040c352b` | `data/calibrations/trial_2026-11-10/ibm_phoenix_properties_update_20261110T131438Z_6331a7c9c5b6.json` | 2026-11-10T11:05:20Z to 2026-11-10T11:05:20Z (1 distinct, n = 120) | 2026-08-25T15:23:25Z to 2026-11-10T11:20:04Z (58 distinct, n = 116) | 2026-10-29T10:53:46Z to 2026-11-10T13:16:59.367698Z (16 distinct, n = 436) | 2026-10-31T05:57:44Z to 2026-11-10T13:16:57Z (8 distinct, n = 120) | 2026-11-07T02:19:57Z to 2026-11-09T20:15:14Z (5 distinct, n = 119) |
| 2026-11-10T13:37:31Z | `ff258e53639b62290fc8f8b5279fc7379abe5f8d7e1e8f234978470e407923c5` | `data/calibrations/trial_2026-11-10/ibm_phoenix_properties_update_20261110T133731Z_ff258e53639b.json` | 2026-11-10T13:37:29Z to 2026-11-10T13:37:31Z (3 distinct, n = 120) | 2026-08-25T15:23:25Z to 2026-11-10T11:20:04Z (58 distinct, n = 116) | 2026-10-29T10:53:46Z to 2026-11-10T13:37:52.187328Z (16 distinct, n = 436) | 2026-10-31T05:57:44Z to 2026-11-10T13:37:50Z (8 distinct, n = 120) | 2026-11-07T02:19:57Z to 2026-11-09T20:15:14Z (5 distinct, n = 119) |
| 2026-11-10T16:34:05Z | `60a212c41b76cf495da0570c911c1a093cd2bbb9f0db66fc75d603da8be1e8b5` | `data/calibrations/trial_2026-11-10/ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json` | 2026-11-10T13:37:29Z to 2026-11-10T13:37:31Z (3 distinct, n = 120) | 2026-08-25T15:23:25Z to 2026-11-10T11:20:04Z (58 distinct, n = 116) | 2026-10-29T10:53:46Z to 2026-11-10T16:37:00.491676Z (16 distinct, n = 436) | 2026-10-31T05:57:44Z to 2026-11-10T16:36:58Z (8 distinct, n = 120) | 2026-11-07T02:19:57Z to 2026-11-09T20:15:14Z (5 distinct, n = 119) |

Calls made: 41 (listed with their outcome in the JSON).
