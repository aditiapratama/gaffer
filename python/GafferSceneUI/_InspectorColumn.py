##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import functools

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from GafferUI.PlugValueWidget import sole
from GafferSceneUI._HistoryWindow import _HistoryWindow

# This file extends the C++ functionality of InspectorColumn with functionality
# that is easier to implement in Python. This should all be considered as one
# component.

def __toggleBoolean( pathListing, inspectors, inspections ) :

	plugs = [ i.acquireEdit() for i in inspections ]
	# Make sure all the plugs either contain, or are themselves a BoolPlug or can be edited
	# by `SetMembershipInspector.editSetMembership()`
	if not all (
		(
			isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) and
			isinstance( plug["value"], Gaffer.BoolPlug )
		) or (
			isinstance( plug, ( Gaffer.BoolPlug ) )
		) or (
			isinstance( inspector, GafferSceneUI.Private.SetMembershipInspector )
		)
		for plug, inspector in zip( plugs, inspectors )
	) :
		return False

	currentValues = []

	# Use a single new value for all plugs.
	# First we need to find out what the new value would be for each plug in isolation.
	for inspector, pathInspections in inspectors.items() :
		for path, inspection in pathInspections.items() :
			currentValues.append( inspection.value().value if inspection.value() is not None else False )

	# Now set the value for all plugs, defaulting to `True` if they are not
	# currently all the same.
	newValue = not sole( currentValues )

	with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
		for inspector, pathInspections in inspectors.items() :
			for path, inspection in pathInspections.items() :
				if isinstance( inspector, GafferSceneUI.Private.SetMembershipInspector ) :
					inspector.editSetMembership(
						inspection,
						path,
						GafferScene.EditScopeAlgo.SetMembership.Added if newValue else GafferScene.EditScopeAlgo.SetMembership.Removed
					)

				else :
					plug = inspection.acquireEdit()
					if isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
						plug["value"].setValue( newValue )
						plug["enabled"].setValue( True )
						if isinstance( plug, Gaffer.TweakPlug ) :
							plug["mode"].setValue( Gaffer.TweakPlug.Mode.Create )
					else :
						plug.setValue( newValue )

	return True

def __editSelectedCells( pathListing, quickBoolean = True ) :

	global __inspectorColumnPopup

	# A dictionary of the form :
	# { inspector : { path1 : inspection, path2 : inspection, ... }, ... }
	inspectors = {}
	inspections = []

	path = pathListing.getPath().copy()
	for selection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		for pathString in selection.paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			with inspectionContext :
				inspection = column.inspector().inspect()

				if inspection is not None :
					inspectors.setdefault( column.inspector(), {} )[pathString] = inspection
					inspections.append( inspection )

	if len( inspectors ) == 0 :
		with GafferUI.PopupWindow() as __inspectorColumnPopup :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Image( "warningSmall.png" )
				GafferUI.Label( "<h4>The selected cells cannot be edited in the current Edit Scope</h4>" )

		__inspectorColumnPopup.popup( parent = pathListing )

		return

	nonEditable = [ i for i in inspections if not i.editable() ]

	if len( nonEditable ) == 0 :
		## \todo Consider removal of this usage of the Editor's context when
		# the toggling code is moved the inspectors.
		with pathListing.ancestor( GafferUI.Editor ).context() :
			if not quickBoolean or not __toggleBoolean( pathListing, inspectors, inspections ) :
				edits = [ i.acquireEdit() for i in inspections ]
				warnings = "\n".join( [ i.editWarning() for i in inspections if i.editWarning() != "" ] )
				# The plugs are either not boolean, boolean with mixed values,
				# or attributes that don't exist and are not boolean. Show the popup.
				__inspectorColumnPopup = GafferUI.PlugPopup( edits, warning = warnings )

				if isinstance( __inspectorColumnPopup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
					__inspectorColumnPopup.plugValueWidget().setNameVisible( False )

				__inspectorColumnPopup.popup( parent = pathListing )

	else :
		with GafferUI.PopupWindow() as __inspectorColumnPopup :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Image( "warningSmall.png" )
				GafferUI.Label( "<h4>{}</h4>".format( nonEditable[0].nonEditableReason() ) )

		__inspectorColumnPopup.popup( parent = pathListing )

def __disablableInspectionTweaks( pathListing ) :

	tweaks = []

	path = pathListing.getPath().copy()
	for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		for pathString in columnSelection.paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			with inspectionContext :
				inspection = column.inspector().inspect()
				if inspection is not None and inspection.editable() :
					source = inspection.source()
					editScope = inspection.editScope()
					if (
						(
							(
								isinstance( source, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) and
								source["enabled"].getValue()
							) or
							isinstance( column.inspector(), GafferSceneUI.Private.SetMembershipInspector )
						) and
						( editScope is None or editScope.isAncestorOf( source ) )
					) :
						tweaks.append( ( pathString, column.inspector() ) )
					else :
						return []
				else :
					return []

	return tweaks

def __disableEdits( pathListing ) :

	edits = __disablableInspectionTweaks( pathListing )
	path = pathListing.getPath().copy()
	with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
		for pathString, inspector in edits :
			path.setFromString( pathString )
			with path.inspectionContext() :
				inspection = inspector.inspect()
				if inspection is not None and inspection.editable() :
					source = inspection.source()

					if isinstance( source, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
						source["enabled"].setValue( False )
					elif isinstance( inspector, GafferSceneUI.Private.SetMembershipInspector ) :
						inspector.editSetMembership( inspection, pathString, GafferScene.EditScopeAlgo.SetMembership.Unchanged )

def __removableAttributeInspections( pathListing ) :

	inspections = []

	path = pathListing.getPath().copy()
	for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		if not columnSelection.isEmpty() and type( column.inspector() ) != GafferSceneUI.Private.AttributeInspector :
			return []
		for pathString in columnSelection.paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			with inspectionContext :
				inspection = column.inspector().inspect()
				if inspection is not None and inspection.editable() :
					source = inspection.source()
					if (
						( isinstance( source, Gaffer.TweakPlug ) and source["mode"].getValue() != Gaffer.TweakPlug.Mode.Remove ) or
						( isinstance( source, Gaffer.ValuePlug ) and len( source.children() ) == 2 and "Added" in source and "Removed" in source ) or
						inspection.editScope() is not None
					) :
						inspections.append( inspection )
					else :
						return []
				else :
					return []

	return inspections

def __removeAttributes( pathListing ) :

	inspections = __removableAttributeInspections( pathListing )

	with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
		for inspection in inspections :
			tweak = inspection.acquireEdit()
			tweak["enabled"].setValue( True )
			tweak["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )

def __selectedSetExpressions( pathListing ) :

	# A dictionary of the form :
	# { path1 : set( setExpression1, setExpression2 ), path2 : set( setExpression1 ), ... }
	result = {}

	# Map of Inspectors to metadata prefixes.
	prefixMap = {
		GafferSceneUI.Private.OptionInspector : "option:",
		GafferSceneUI.Private.AttributeInspector : "attribute:"
	}

	path = pathListing.getPath().copy()
	for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		if (
			not columnSelection.isEmpty() and (
				type( column.inspector() ) not in prefixMap.keys() or
				not (
					Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), "ui:scene:acceptsSetName" ) or
					Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), "ui:scene:acceptsSetNames" ) or
					Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), "ui:scene:acceptsSetExpression" )
				)
			)
		) :
			# We only return set expressions if all selected paths are in
			# columns that accept set names or set expressions.
			return {}

		for pathString in columnSelection.paths() :
			path.setFromString( pathString )
			cellValue = column.cellData( path ).value
			if cellValue is not None :
				result.setdefault( pathString, set() ).add( cellValue )
			else :
				# We only return set expressions if all selected paths have values.
				return {}

	return result

def __selectAffected( pathListing ) :

	result = IECore.PathMatcher()

	editor = pathListing.ancestor( GafferUI.Editor )
	path = pathListing.getPath().copy()

	for pathString, setExpressions in __selectedSetExpressions( pathListing ).items() :
		# Evaluate set expressions within their path's inspection context
		# as set membership could vary based on the context.
		path.setFromString( pathString )
		with path.inspectionContext() :
			for setExpression in setExpressions :
				result.addPaths( GafferScene.SetAlgo.evaluateSetExpression( setExpression, editor.settings()["in"] ) )

	GafferSceneUI.ContextAlgo.setSelectedPaths( editor.scriptNode().context(), result )

def __showHistory( pathListing ) :

	columns = pathListing.getColumns()
	selection = pathListing.getSelection()
	path = pathListing.getPath().copy()

	for i, column in enumerate( columns ) :
		for pathString in selection[i].paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			window = _HistoryWindow(
				column.inspector(),
				pathString,
				inspectionContext,
				pathListing.ancestor( GafferUI.Editor ).scriptNode(),
				"History : {} : {}".format( pathString, column.headerData().value )
			)
			pathListing.ancestor( GafferUI.Window ).addChildWindow( window, removeOnClose = True )
			window.setVisible( True )

def __validateSelection( pathListing ) :

	selection = pathListing.getSelection()
	# We only operate on PathListingWidgets
	# with `Cell` or `Cells` selection modes.
	if not isinstance( selection, list ) :
		return False

	if all( [ x.isEmpty() for x in selection ] ) :
		return False

	for columnSelection, column in zip( selection, pathListing.getColumns() ) :
		if not columnSelection.isEmpty() and not isinstance( column, GafferSceneUI.Private.InspectorColumn ) :
			return False

	return True

def __buttonDoubleClick( path, pathListing, event ) :

	# We only support doubleClick events when all of the selected
	# cells are in InspectorColumns.
	if not __validateSelection( pathListing ) :
		return False

	if event.button == event.Buttons.Left :
		__editSelectedCells( pathListing )
		return True

	return False

def __contextMenu( column, pathListing, menuDefinition ) :

	# We only add context menu items when all of the selected
	# cells are in InspectorColumns.
	if not __validateSelection( pathListing ) :
		return

	menuDefinition.append(
		"Show History...",
		{
			"command" : functools.partial( __showHistory, pathListing )
		}
	)

	toggleOnly = isinstance( column.inspector(), GafferSceneUI.Private.SetMembershipInspector )
	menuDefinition.append(
		"Toggle" if toggleOnly else "Edit...",
		{
			"command" : functools.partial( __editSelectedCells, pathListing, toggleOnly ),
		}
	)
	menuDefinition.append(
		"Disable Edit",
		{
			"command" : functools.partial( __disableEdits, pathListing ),
			"active" : len( __disablableInspectionTweaks( pathListing ) ) > 0,
			"shortCut" : "D",
		}
	)

	if len( __removableAttributeInspections( pathListing ) ) > 0 :
		menuDefinition.append(
			"Remove Attribute",
			{
				"command" : functools.partial( __removeAttributes, pathListing ),
				"shortCut" : "Backspace, Delete",
			}
		)

	if len( __selectedSetExpressions( pathListing ) ) > 0 :
		menuDefinition.append(
			"SelectAffectedObjectsDivider", { "divider" : True }
		)
		menuDefinition.append(
			"Select Affected Objects",
			{
				"command" : functools.partial( __selectAffected, pathListing ),
			}
		)

def __keyPress( column, pathListing, event ) :

	# We only support keyPress events when all of the selected
	# cells are in InspectorColumns.
	if not __validateSelection( pathListing ) :
		return

	if event.modifiers == event.Modifiers.None_ :
		if event.key in ( "Return", "Enter" ) :
			__editSelectedCells( pathListing )
			return True

		if event.key == "D" :
			if len( __disablableInspectionTweaks( pathListing ) ) > 0 :
				__disableEdits( pathListing )
			return True

		if event.key in ( "Backspace", "Delete" ) :
			if len( __removableAttributeInspections( pathListing ) ) > 0 :
				__removeAttributes( pathListing )
			return True

	return False

def __inspectorColumnCreated( column ) :

	if isinstance( column, GafferSceneUI.Private.InspectorColumn ) :
		column.buttonDoubleClickSignal().connectFront( __buttonDoubleClick, scoped = False )
		column.contextMenuSignal().connectFront( __contextMenu, scoped = False )
		column.keyPressSignal().connectFront( __keyPress, scoped = False )

GafferSceneUI.Private.InspectorColumn.instanceCreatedSignal().connect( __inspectorColumnCreated, scoped = False )
