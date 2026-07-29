# List Pickable Filters — GetFilterList

Lists the **saved filters** a user can choose for a given **project + work-item type**. Use it
to turn a "type the filter ID" field into a **searchable dropdown** — the user picks a filter by
name and you store its numeric `Id` (nothing else changes downstream).

> ⚠️ **Not every tenant has this endpoint.** It exists on some Orcanos instances and not others.
> **Never assume it's present.** Treat a 404 (or any non-array response) as "API not available"
> and **fall back to a manual filter-ID input** — that is the expected state, not an error. This
> is the whole reason the feature is optional.

**Reference:** https://help.orcanos.com/knowledgebase/

---

## Endpoint

```
GET  <base>/api/v2/Json/GetFilterList?ProjectId=<id>&ItemType=<Type Description>
Authorization: Basic <base64(username:password)>  OR  Bearer <api-key>
Content-Type: application/json
```

e.g. `…/GetFilterList?ProjectId=7506&ItemType=Software%20Requirement` — the **description**,
not `SRS`.

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Auth: same options as every endpoint — see [SKILL.md](SKILL.md).

---

## Request Parameters (query string)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ProjectId` | integer | **Yes** | The project's numeric id, e.g. `7506`. |
| `ItemType` | string | **Yes** | The work-item **DESCRIPTION / Label** — e.g. `Software Requirement`, `Test Case`. ⚠️ **Not** the original code (`SRS`, `T_CASE`) and **not** the custom-code prefix (`SR`). This scopes which filters come back. |

> 🐛 **This is the trap.** `GetFilterList` matches on the type's **display name**, unlike almost
> every other Orcanos endpoint (`get_filter_results`' `Item_Type`, `GetItemURL`'s `Item`, the
> relation keys — those all take the **code**). Passing the code here does **not** error: it
> returns **`200` with an empty array**, which is indistinguishable from "this project has no
> saved filters" — so the picker silently degrades to a manual ID input and the bug reads as
> "the tenant doesn't have the API". Resolve the Label from `QW_Login` →
> `Data.Projects.Project[].Item_type[].Label` for the code you hold, and send that.

The swagger form for this endpoint shows exactly two fields: **ProjectId** and **ItemType**.
There is **no version parameter** — filters are scoped by project + type only.

---

## Response

⚠️ **A bare JSON array** — NOT the usual `{ "IsSuccess": ..., "Data": ... }` wrapper the `QW_*`
endpoints return. The presence of a top-level array is itself the "API is available" signal.

```json
[
  {
    "Id": 760,
    "Name": "{Embedded Filter} My Children",
    "ProjectId": -1,
    "Owner": "orca",
    "Public": "Y",
    "Private": "N",
    "ObjType": "ALL",
    "LabelID": 0,
    "LabelName": "",
    "FilterLabelMappingUserID": 0,
    "IsSystemFilter": false,
    "IsDesktop": 0,
    "IsEditRights": 1,
    "ReportLevel": ""
  },
  {
    "Id": 683,
    "Name": "{embedded} All Related items to $ME",
    "ProjectId": -1,
    "ObjType": "ALL",
    "Public": "Y",
    "...": "..."
  }
]
```

### Fields that matter

| Field | Meaning |
|---|---|
| `Id` | The filter id — **this is what you save** (it's the `filter_id` the matrix engine uses). |
| `Name` | Human label to show in the dropdown. **Not unique** — show the id alongside it (e.g. `My Filter (#760)`). |
| `ProjectId` | The project the filter belongs to. **`-1` means an embedded / global filter** that applies to every project — these are always returned. Otherwise it's a specific project id. |
| `ObjType` | `"ALL"`, or a specific original **code** (e.g. `"SRS"`) — note the response speaks codes even though the *request* takes the label. Because you pass `ItemType`, the server already returns the applicable set (ALL + that type) — **no client-side `ObjType` filtering needed.** |
| `Public` | `"Y"` / `"N"`. |

---

## Availability detection (critical)

Infer availability; do not assume it:

| Result | Interpretation | Action |
|---|---|---|
| `200` + JSON **array** | API available | Show the dropdown |
| `200` + **empty** array | Either no filters, **or you sent the code instead of the description** | Check `ItemType` first — see the trap above |
| `404` | Endpoint not on this tenant | **Fall back to a manual filter-ID input** |
| Any other non-200, or a non-array 200 body, or a transport error | Can't use it | **Fall back to a manual filter-ID input** |
| `401` | Session expired | Re-authenticate (generic 401 handling) |

Never surface a hard error for a missing endpoint — a manual ID input is the graceful default,
identical to the pre-feature behaviour.

---

## Reference implementation (this project)

- **Client:** `OrcanoClient.get_filter_list(auth_header, project_id, item_type)` in
  `src/backend/orcanos_client.py` — GETs the endpoint, returns
  `{"available": bool, "filters": [...]}`. `item_type` here is the **Label**. Any non-array /
  non-200 / exception ⇒ `available: False`.
- **Backend route:** `GET /api/config/filters?project_id=&item_type=&item_type_label=` in
  `src/backend/config_api.py` — `item_type` stays the **code** (that's what a panel stores);
  `item_type_label` is the description the caller already knows. When the label isn't supplied,
  `_resolve_type_label()` looks it up live from `QW_Login`. Maps the raw filters to
  `{id, name, obj_type, project_id, public}` and returns `{available, filters}`; returns
  `available: False` (never a 4xx/5xx) when the API is absent.
- **Frontend:** `FilterSelect` in `src/frontend/src/pages/ConfigPage.jsx` — renders a
  `SearchableSelect` when `available && filters.length`, else a plain number input. It passes
  `itemTypeLabel` (the level's stored `work_item_type_label`, else the code→label lookup) and
  writes the selected filter's **id** back into the same `filter_id` field, so the saved panel
  shape is unchanged. Fetches are cached per `(project_id, item_type)` and shared by every
  filter field (base, per-level, orphans).

### Example call

```python
# Resolve the DESCRIPTION for the code you hold, from QW_Login's Item_type[]
label = "Software Requirement"                       # NOT "SRS"
res = await client.get_filter_list(auth_header, project_id=7506, item_type=label)
if res["available"]:
    for f in res["filters"]:
        print(f["Id"], f["Name"], f["ObjType"])   # 760 "{Embedded Filter} My Children" ALL
else:
    # tenant has no GetFilterList — let the user type the filter id
    ...
```

---

## Gotchas

- **Pass the description (Label), not the code or custom prefix.** `ItemType=Software Requirement` works; `ItemType=SRS` or `ItemType=SR` returns an empty list. This endpoint is the **exception** — everywhere else in this API the type is the code, so it's easy to get wrong and the failure is silent.
- **An empty array is ambiguous** — "no filters" and "wrong ItemType" look identical. Always sanity-check the type string before concluding the tenant has none.
- **`Name` is not unique** — always disambiguate with the `Id` in any picker.
- **Don't over-filter on `ObjType`.** You already scoped by `ItemType` in the request; dropping non-matching `ObjType` rows client-side can hide valid `ALL` filters.
- **Bare array, no `IsSuccess`.** Code that blindly reads `data["Data"]` or `data["IsSuccess"]` will break — handle the top-level list.
