| **Specification**                          | **Specification source** | **Test**                                             |
| ------------------------------------------ | ------------------------ | ---------------------------------------------------- |
| POST /api/create-user                      | api.md                   | test_api.py                                          |
| POST /api/login                            | api.md                   | test_api.py, test_regression_a03.py                  |
| GET /api/healthz                           | api.md                   | test_api.py                                          |
| POST /api/upload-document                  | api.md                   | test_baseline_a02.py, test_regression_a01.py         |
| GET /api/list-documents                    | api.md                   | test_api.py                                          |
| DELETE /api/delete-document/<document_id>  | server.py                | test_delete_document.py                              |
| GET /api/get-document/<document_id>        | api.md                   | test_delete_document.py, test_security_monitoring.py |
| GET /api/list-versions/<document_id>       | api.md                   | test_list_versions.py                                |
| GET /api/list-all-versions                 | api.md                   | test_list_all_versions.py                            |
| POST /api/create/watermark/<document_id>   | api.md                   | test_baseline_a02.py, test_regression_a02.py         |
| POST /api/read-watermark                   | api.md                   | test_read_watermark.py                               |
| POST /api/read-watermark/<document_id>     | api.md                   | test_read_watermark_document_id.py                   |
| GET /api/get-watermarking-methods          | api.md                   | test_get_watermarking_methods.py                     |
| GET /api/get-version/<link>                | server.py                | test_rmap_e2e.py, test_get_version.py                |
| POST /api/rmap-initiate                    | api.md                   | test_rmap_api.py, test_rmap_e2e.py                   |
| POST /api/rmap-get-link                    | api.md                   | test_rmap_api.py, test_rmap_e2e.py                   |
