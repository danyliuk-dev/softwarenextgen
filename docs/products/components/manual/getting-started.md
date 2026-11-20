# Getting started

[Manual](README.md) · [Code examples](code-examples.md)

NextgenComponents is a UI library. Your application owns data, persistence, authentication and external AI calls. Use the components in an existing host or run the included galleries as complete working applications.

## Blazor: install and host

Install and open NextgenComponents first; see [Installation](/docs/components/installation). To develop your own Blazor application, install .NET SDK 10. The gallery itself needs no SDK. Copy `SDK` from the installed resources into your application as `vendor/nextgen-sdk`. From your application directory, add the prebuilt package:

```bash
dotnet add package NextgenComponents.Blazor --version 0.74.1 --source ./vendor/nextgen-sdk/NuGet
```

Add `@using NextgenComponents.Blazor` to `_Imports.razor`. In the host document include:

```html
<link rel="stylesheet" href="_content/NextgenComponents.Blazor/nextgen.css" />
```

Register interactive rendering in `Program.cs` (using your application's App component):

```csharp
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
// After builder.Build(), use your normal middleware and static asset setup.
app.MapStaticAssets();
app.MapRazorComponents<App>().AddInteractiveServerRenderMode();
```

The host must load `_framework/blazor.web.js`. NuGet supplies the component assembly and static web assets together. Keep `app.MapStaticAssets()` in your host; do not reference the gallery executable or copy individual DLLs.

Create a Razor page:

```razor
@page "/example"
@using NextgenComponents.Blazor
@using static Microsoft.AspNetCore.Components.Web.RenderMode
@rendermode InteractiveServer
<div class="ng-scope" data-ng-theme="light" data-ng-density="normal">
    <NgTextBox Label="Name" @bind-Value="name" />
    <NgButton Primary OnClick="Save">Save</NgButton>
    <p>@status</p>
</div>
@code {
    private string? name;
    private string? status;
    private void Save() => status = $"Hello, {name}";
}
```

If the host already makes routes interactive, omit the page's `@rendermode`. Static SSR alone renders markup but does not run browser event callbacks.

`@bind-Value` supplies Value, ValueChanged and ValueExpression. With manual binding to InputBase/InputSelect/InputNumber wrappers, provide `ValueExpression="()=>model.Field"`, even outside a form. For a string parameter use `Value="@variable"`; `Value="variable"` may pass literal text.

Apply `data-ng-theme="light"` or `"dark"` and `data-ng-density="normal"` or `"compact"` to the outer `.ng-scope`. Shared tokens keep colors and focus states consistent.

## Flutter: install and host

For your own application, use Flutter >= 3.38 and Dart >= 3.10. Copy the installed `SDK/Flutter/nextgen_components` directory into `vendor/nextgen_components` in your application. Add a dependency relative to your application's pubspec.yaml:

```yaml
dependencies:
  flutter:
    sdk: flutter
  nextgen_components:
    path: vendor/nextgen_components
```

Run `flutter pub get`. A complete application shell:

```dart
import 'package:flutter/material.dart';
import 'package:nextgen_components/nextgen_components.dart';

void main() => runApp(MaterialApp(
  theme: NgTheme.light(), darkTheme: NgTheme.dark(),
  home: const Demo(),
));
class Demo extends StatefulWidget {
  const Demo({super.key});
  @override State<Demo> createState() => _DemoState();
}
class _DemoState extends State<Demo> {
  bool enabled = true;
  @override Widget build(BuildContext context) => Scaffold(
    body: Padding(padding: const EdgeInsets.all(24), child: NgSwitch(
      label: 'Notifications', value: enabled,
      onChanged: (v) => setState(() => enabled = v),
    )),
  );
}
```

Use `NgTheme.light(compact: true)` and its dark equivalent for compact density. Component-page Flutter examples are fields and methods inside a State class such as `_DemoState`; do not combine several build methods. Import Material for Text, Widget and BuildContext.

Most components use `value → action → onChanged → setState → new value`. Store callback values or the component will retain the old state. For text fields, initialValue is only the initial draft. Use TextEditingController for programmatic changes, never combine it with initialValue, and dispose it in its owner.

## Forms and persistence

1. Keep an editable draft separate from the saved record.
2. Wrap validated fields in NgForm: DataAnnotations in Blazor, validator/required in Flutter.
3. On successful validation call your own save service. Display network errors separately from field parsing errors.
4. Cancel discards the draft; Save replaces the changed record and its collection.
5. Use stable unique IDs and replace input collections instead of mutating them silently.

Blazor dates use DateOnly/TimeOnly/DateTime; Flutter uses DateTime/TimeOfDay. Normalize timezones at application boundaries.

## Run the included applications

Open **NextgenComponents**, then **Workspace → Blazor gallery** or **Workspace → Flutter gallery**. Select a component, change its values and compare the result with **Code examples**. Open **Workspace → Documentation** for the same manuals offline. The installed launcher chooses and starts the local server automatically. No terminal, repository checkout or library build is needed.
