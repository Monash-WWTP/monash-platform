# Public final-effluent snapshot

Snapshot 1.1.0 contains one station, 154 final-effluent samples (2023–2025), and eight emission-factor reference rows. CSVs and `manifest.json` are byte-identical to the pinned dashboard source. The [dictionary](DATA_DICTIONARY.md) explains fields and BDL flags. No derived GHG dataset is included.

The inherited [CC BY 4.0 license](LICENSE-DATA) applies to the relocated dataset formerly under `public-data/`. It does not license application software or the separately held raw source CSVs. Attribute the dataset to Lai Jien Weng and Chow Ming Fai, Monash University Malaysia, using the source project's attribution; cite the Monash-WWTP/wwtp-dashboard repository, snapshot version 1.1.0, manifest timestamp, and source revision recorded in the manifest/inventory. No DOI is supplied or invented.

The historical CITATION.cff predates this snapshot and describes derived GHG intensities that are absent here. Use the final-effluent snapshot description above. The manifest's `source_commit` is the original exporter revision; the import pin is `202b72e`, as recorded in the source inventory. New analysis must preserve this distinction.

Source compliance labels are not independently checked permit decisions. Reference factors do not establish applicability to this site's measured emissions. See [scientific limits](../../docs/science/VALIDATION.md). Future refreshes need explicit column allowlists, rights/privacy review, versioning and a reviewed manifest; the legacy live helper is inactive.
