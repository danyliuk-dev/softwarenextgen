# TypeScript and report events

Start with the [authoring manual](report-authoring-manual.md), then use this guide
for typed report logic and dialog handlers. Code examples retain the actual API
contracts; define the parameters/components mentioned before running them.

## Contract v1

Optional logic.source contains TypeScript, language is typescript and apiVersion is 1.
The server compiles source and checks types; client-supplied JavaScript is not accepted.
Export named synchronous handlers only; helper functions must not be exported.
validateParameters runs after parameter types/defaults and returns ValidationError[].
beforeRender returns replacement JSON data; afterRender runs after layout and returns
void. Missing handlers are skipped. Each render owns a Jint environment; report
events within that render share it. An exception stops later stages.

```json
{
  "logic": {
    "language": "typescript",
    "apiVersion": 1,
    "source": "export function validateParameters(ctx: ReportContext): ValidationError[] { return []; }"
  }
}
```

## Context types

ReportParameters comes from template definitions and ReportData from input JSON.
Inference examines five levels, 100 properties/object, 20 elements/array and 1,000
nodes overall; deeper data and empty-array elements use JsonValue. Narrow types
for heterogeneous values. Optional numbers/booleans without values may be an empty
string: check it or supply defaults. Types describe the input, not fields created
by beforeRender. afterRender receives prepared data, but new fields require explicit
narrowing. Parameters are read-only; returned data does not overwrite the user's JSON.

```ts
interface ReportContext {
  readonly parameters: Readonly<ReportParameters>;
  readonly data: ReportData;
}
interface AfterRenderContext extends ReportContext {
  readonly result: { readonly title: string; readonly pageCount: number; };
}
interface ValidationError {
  parameter: keyof ReportParameters;
  message: string;
}
type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
interface JsonObject { [key: string]: JsonValue; }
```

## validateParameters

Define numeric minimumQuantity before using this example. Return an empty array
for success. Each parameter must exist; messages must be nonempty and at most 2,000
characters, with at most 100 errors. API failures are HTTP 400 Problem Details with
parameterErrors. Studio marks fields. Basic required/type validation runs first.

```ts
export function validateParameters(ctx: ReportContext): ValidationError[] {
  if (!Number.isInteger(ctx.parameters.minimumQuantity) ||
      ctx.parameters.minimumQuantity < 0) {
    return [{
      parameter: "minimumQuantity",
      message: "Enter a whole number of zero or greater."
    }];
  }
  return [];
}
```

## beforeRender

Use the inventory sample, or define items with numeric quantity and a numeric
minimumQuantity parameter. Bind {{data.selectedCount}} and table source items.
Return all original fields still needed by the report. undefined, Promise, array
and scalar results are rejected; the result must be a JSON object of at most 8 MB.
Unlike Data → Table, these transformations affect output. For money, calculate exact
amounts in the host or use safe integer minor units; JavaScript Number is binary
floating point and no decimal script helpers are provided.

```ts
export function beforeRender(ctx: ReportContext): JsonObject {
  const items = ctx.data.items.filter(
    item => item.quantity >= ctx.parameters.minimumQuantity
  );
  return { ...ctx.data, items, selectedCount: items.length };
}
```

## afterRender

This means layout completed, not that PDF writing or delivery succeeded. Do not
place payments, database writes or message delivery here. Preview and export are
separate executions. Pass dates/seeds explicitly for reproducible output.

```ts
export function afterRender(ctx: AfterRenderContext): void {
  if (ctx.result.pageCount > 10) {
    throw new Error("Narrow the selection: this report is limited to 10 pages.");
  }
}
```

## Monaco Editor

Page → Code offers highlighting, completion, hover and local diagnostics.
Insert event adds a handler without replacing existing source. Check code performs
a strict server check with line/column diagnostics; Apply code saves the draft,
and empty source removes logic. Designer Undo reverts the application as one edit.
Opening/checking does not run events. Monaco 0.52.2 and server TypeScript 5.9.3
can report different diagnostics; server Check code is authoritative. Recheck
after changing parameters or data to refresh declarations.

## Install and run

Install and open **Nextgen Reports**. The editor, compiler files and runtime are bundled. Enable trusted scripts using the installed application launch commands in the [Desktop guide](desktop.md#trusted-report-scripts). No product build or npm install is required.

For a separate integration engine, use the executable launch from the [developer guide](developer-guide.md#start-the-installed-engine-for-integration). Enable `NEXTGEN_ENABLE_SCRIPTS=1` and point `NEXTGEN_NODE` to a Node.js 22+ executable. The normal desktop launcher already supplies its bundled Node runtime. Only enable scripts for trusted templates; a template with logic fails when script execution is disabled.

## Limits and trust

Source: 64,000 characters. Compiler: separate Node process, 256 MB JS heap,
15-second timeout. Jint: 100,000 statements, 32 MB accounted memory, call depth 64
and two seconds per engine entry; cancellation is supported. No CLR, filesystem,
network, host objects, imports/re-exports, npm, DOM or Node APIs. Async, per-block
or per-page events, debugger and custom C# libraries are not implemented.
Interpreter limits are not an OS sandbox or an exhaustion guarantee. Public
workloads need isolated workers, OS quotas, authorization and queuing. These hosts
can serve Blazor/Flutter but do not provide an offline mobile runtime.

## Checking and automation

POST /api/logic/check accepts {template,data,parameters?} and returns
{enabled,declarations,diagnostics}. Type errors are diagnostics with HTTP 200;
request/compiler failures use HTTP 400. Checking does not execute scripts.
Edit logic.source, check, render with real sample inputs and inspect the PDF.
The readable inventory.logic.ts copy must remain synchronized with source in
inventory.nrtemplate. Compiler references: TypeScript Compiler API, Monaco and Jint.

Use **Check code**, then generate Preview with both valid and invalid parameter values. Inspect diagnostics and confirm the expected event behavior.

## Parameter input dialog

Run with parameters opens a private value draft. Cancel discards it; Generate
runs server validation and report events. Errors keep the dialog open; success
commits values. Page → Parameters configures Label (200 characters), Help text
(2,000), Control and defaults. Multiline requires string; Auto follows value type.
Layout belongs to Dialogs and does not change types. ComboBox options are 0–200
unique nonempty strings, up to 500 characters, with exact case/space matching.
Defaults must match an option unless optional/empty. Static choices are checked
before scripts. Dynamic choices use DialogUpdate.options.

## Visual dialog editor

Create parameters, then Dialogs → Create form (automatic placement for up to 12
parameters). Move on the 8 px grid, resize using handles or edit geometry in
Properties. Toolbox fields reuse compatible unbound parameters or create parameterN;
ComboBox starts with two choices. Preview form never executes scripts; Run with
parameters does. One form supports 100 components. Geometry uses CSS pixels,
independent of report page points. Narrow screens stack controls.

Only placed fields appear; hidden/unplaced values still undergo server validation.
A parameter can bind once. Remove its bound field before deleting its definition.
Remove form preserves parameter definitions/values. Containers own child bounds,
movement and anchors; see the Toolbox guide for tabs and nesting.

Align commands use parent bounds. Arrows move 1 px, Shift+arrows 8 px. Earlier/Later
controls sibling tab/painting/stack order; labels do not receive focus. Select
Form in the tree to edit title/size. Right-click or Shift+F10 opens actions;
Delete and Ctrl/Command+D delete/duplicate. Containers delete descendants while
preserving parameter definitions. Copy/cut/paste and Undo/Redo operate on layouts.
See the English authoring manual for the complete workspace exercise.

## Extended Toolbox

Use the grouped searchable palette for fields, containers, display controls and
actions. Each tool has a local icon and supports click insertion/dragging. Component
properties determine bounds, parent, anchors, bindings and action. See
[Dialog Toolbox](toolbox.md) for all 30 entries, contracts and limits.
Deleting fields does not delete their parameters. Preview shows layout without
scripts; runtime uses the actual parameter controls and validation.

## Dialog Load and Change

Define quantity:number and caption:string for the examples. Dialogs → Code inserts
typed handlers; Apply code then Run report. dialogLoad runs on open/Reset;
parameterChanged follows the browser change event, not each keystroke. ctx.parameter
is the parameter name. Context is immutable; return a DialogUpdate patch. Empty
objects change nothing; patches do not recursively trigger Changed. Each event
has a fresh execution environment.

Draft fields may be empty, including numeric fields. The server checks names/types;
required/range/final rules run at Generate. Unrepresentable control values reject
the whole patch. Controls are blocked during requests but Cancel remains available,
aborts the request and discards the draft. Errors block Generate until a successful
event or reopening. Only successful generation commits values.

Changed preserves field/choice focus when possible, without stealing focus back
from a user who moved elsewhere. Range readouts follow both input and patches.
POST /api/dialog/event accepts {template,data,parameters,event,parameter?}; scripts
must be enabled. Messages: 2,000 characters, response: 256 KB, one value: 64,000
JSON characters, arrays: 200 strings. Unknown fields/types fail atomically. Code
compiles on every call, so latency can be noticeable. Exercise dialog events in the installed Studio with representative input values.

```ts
// Parameters: quantity: number and caption: string.
export function dialogLoad(ctx: DialogContext): DialogUpdate {
  return { parameters: { quantity: 2 }, message: "Ready" };
}
export function parameterChanged(ctx: ParameterChangedContext): DialogUpdate {
  if (ctx.parameter !== "quantity") return {};
  return { parameters: { caption: "Quantity: " + ctx.parameters.quantity } };
}
```

## Custom buttons: Click

Insert Button · Custom, set its unique ID to calculate, then Code → Button click
and Apply code. Run report and click it: the form stays open. The example uses
quantity and caption. One handler distinguishes all buttons by ctx.componentId;
it returns the same atomic DialogUpdate as Load/Change. Preview form skips Click.
Submit/Reset/Cancel retain their own actions. Missing handlers prompt the user to
open Code. API event dialogButtonClick requires componentId naming exactly one
button with action custom; missing/duplicate/wrong-kind IDs fail.

```ts
export function dialogButtonClick(ctx: DialogButtonContext): DialogUpdate {
  if (ctx.componentId !== "calculate") return {};
  return {
    parameters: { caption: "Quantity: " + ctx.parameters.quantity },
    message: "Calculated"
  };
}
```

## Component visibility and availability

components keys are existing component IDs; visible/enabled must be booleans.
Unknown/duplicate IDs or unsupported properties reject the entire response.
Individual TabPages cannot be patched; TabControl/Panel/GroupBox state affects
children. Omitted properties retain state; true restores a field only when its
ancestors allow it. Value patches preserve state. Hidden/disabled values still
undergo final required/parameter validation, so supply required values or fix logic.
State is transient: Cancel, Reset and reopen clear it. Templates do not change;
Preview form executes no handlers.

```ts
export function dialogLoad(): DialogUpdate {
  return {
    components: {
      captionField: { visible: false },
      detailsGroup: { enabled: false }
    }
  };
}
```

## Dynamic choices

options keys are parameter names and values are string arrays for Select/List/
Radio/CheckedList. Read choices from ctx.data; scripts cannot fetch network data.
The example requires country/city and a cities object with Ukraine and Poland arrays.
Limits: 0–200 unique nonblank single-line values, up to 500 characters. Invalid
names/control/types/duplicates/limits reject the whole response. Empty options do
not waive Required.

Without a parameter patch, still-valid choices remain; removed single choices
become empty and CheckedList retains the intersection in new-option order.
Explicit selections must belong to new options in the same response. Later value
patches validate against current choices. Recreated controls retain state/labels/help.
Cancel discards draft choices; Reset starts from the template then runs Load.
Preview form uses static choices. Generate commits effective options for the
current session and sidebar; changing source data/template invalidates them.
Studio submits a template copy with current options for validation/rendering.
Save project preserves effective choices/values; Save template preserves original
definitions and event logic. Dependencies recalculate in Run report, not sidebar edits.

```ts
export function dialogLoad(ctx: DialogContext): DialogUpdate {
  const cities = ctx.parameters.country === "Poland"
    ? ctx.data.cities.Poland : ctx.data.cities.Ukraine;
  return { options: { city: cities } };
}
export function parameterChanged(ctx: ParameterChangedContext): DialogUpdate {
  if (ctx.parameter !== "country") return {};
  const cities = ctx.parameters.country === "Poland"
    ? ctx.data.cities.Poland : ctx.data.cities.Ukraine;
  return { options: { city: cities }, parameters: { city: "" } };
}
```

## Dialog page changed

dialogPageChanged runs after switching to a different TabPage using mouse or
ArrowLeft/Right/Home/End. ctx.componentId names that page, not the TabControl.
Return DialogUpdate. Initial selection, reselecting the current page, revealing
validation errors and Preview form skip the event. During the request navigation
is blocked. Failure keeps the destination page but blocks Generate until recovery
or reopen. Missing handler is allowed. IDs must name a unique TabPage belonging
to one TabControl. Use dialogPageChanging to veto before transition.

```ts
export function dialogPageChanged(ctx: DialogPageContext): DialogUpdate {
  return { message: "Selected page: " + ctx.componentId };
}
```

## Back and Next buttons

Insert a button inside a TabPage (possibly nested in a panel/group), set action
next/back and caption Next/Back. It navigates sibling pages in the nearest owning
TabControl; endpoints disable unavailable directions. Next validates required and
browser-valid fields on the current page before transition; Back permits incomplete
fields. Final Generate still validates all parameters. Successful navigation runs
Page changing then Page changed. Preview form navigates without scripts.
These are navigation actions, not Custom Click. Undo/Redo and saved templates retain them.

## Sequential steps

Enable Sequential steps on TabControl to require Next for forward navigation.
Current and previous page headers remain reachable; later headers/keyboard jumps
are blocked. Backtracking blocks forward access again rather than recording a
permanent completion flag. Next performs current-page validation; Back does not.
Each nested TabControl has its own sequence. Initial selection, error reveal and
Preview form retain their documented behavior; final report validation remains
independent. This is form navigation, not authorization.

## Events in Properties

Select Form, a bound field, Custom button or TabPage, then use Properties → Events
to open its typed handler. Existing handlers are shared across the report and are
opened without overwriting source. Branch on parameter/componentId; do not define
multiple exports with the same name. Check code then Apply, and exercise the real
runtime form. Preview form does not prove script behavior.

## Validate before navigation: dialogPageChanging

The destination is ctx.componentId and the source is previousComponentId.
Return {cancel:true,message:...} to veto, or {} to allow. Results accept only
cancel/message, not parameter/options/component patches; use Page changed after
arrival for updates. Next order: browser field validation → Page changing →
transition → Page changed. A veto preserves page and values and is not a script
error. Exceptions preserve the page and block Generate until recovery/reopen.
Controls are blocked while waiting; Cancel can close the form. Late responses
cannot change a subsequently reopened form. Initial opening, validation-error
reveals and Preview form skip this hook. Generate performs full independent
validation; a navigation veto is not a substitute for validateParameters.

```ts
export function dialogPageChanging(ctx: DialogPageChangingContext): DialogNavigationResult {
  if (ctx.componentId === "confirmation" && ctx.parameters.approval !== "yes") {
    return { cancel: true, message: "Approval is required before confirmation." };
  }
  return {};
}
```
