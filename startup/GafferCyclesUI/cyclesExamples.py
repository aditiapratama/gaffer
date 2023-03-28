import Gaffer
import GafferUI
import GafferCycles
import GafferDispatch
import GafferImage
import GafferScene

GafferUI.Examples.registerExample(
	"Rendering/Wedge Tests",
	"$GAFFER_ROOT/resources/examples/rendering/wedgeTests.gfr",
	description = "Demonstrates how to use the Wedge node to render shader wedge tests.",
	notableNodes = [
		GafferDispatch.Wedge,
		GafferDispatch.SystemCommand,
		GafferImage.Text,
		GafferScene.Outputs,
		Gaffer.ContextVariables,
		Gaffer.ContextQuery,
		Gaffer.Expression,
		GafferCycles.CyclesRender
	]
)

GafferUI.Examples.registerExample(
	"Compositing/Contact Sheet Generation",
	"$GAFFER_ROOT/resources/examples/compositing/contactSheet.gfr",
	description = "Demonstrates how to use the Loop node to build a contact sheet of shader variations.",
	notableNodes = [
		Gaffer.Loop,
		GafferDispatch.Wedge,
		GafferImage.ImageTransform,
		GafferImage.ImageWriter,
		Gaffer.ContextQuery,
		Gaffer.Expression
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Per-location Light Tweak Spreadsheet",
	"$GAFFER_ROOT/resources/examples/rendering/perLocationLightTweakSpreadsheet.gfr",
	description = """
	Demonstrates how to use the Spreadsheet node to vary light tweaks
	per location.
	""",
	notableNodes = [
		Gaffer.Spreadsheet,
		GafferScene.ShaderTweaks,
		GafferCycles.CyclesLight
	]
)
