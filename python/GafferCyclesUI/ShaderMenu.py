##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import collections

import IECore

import GafferUI
import GafferCycles

def appendShaders( menuDefinition, prefix="/Cycles" ) :

	MenuItem = collections.namedtuple( "MenuItem", [ "menuPath", "nodeCreator" ] )

	# Build a list of menu items we want to create.

	menuItems = []

	shaderName = "output"
	displayName = "Output"
	menuPath = "Shader"

	nodeCreator = functools.partial( __shaderCreator, shaderName, GafferCycles.CyclesShader )
	menuItems.append( MenuItem( "%s/%s" % ( menuPath, displayName ), nodeCreator ) ) 

	for shader in GafferCycles.shaders :
		shaderName = str( shader )
		displayName = " ".join( [ IECore.CamelCase.toSpaced( x ) for x in shaderName.split( "_" ) ] )
		category = GafferCycles.shaders[shader]["category"]
		menuPath = "Shader"

		nodeCreator = functools.partial( __shaderCreator, shaderName, GafferCycles.CyclesShader )
		menuItems.append( MenuItem( "%s/%s/%s" % ( menuPath, category, displayName ), nodeCreator ) ) 

	for light in GafferCycles.lights :
		shaderName = str( "%s_light" % light )
		if light == "portal" :
			shaderName = str( light )
		displayName = " ".join( [ IECore.CamelCase.toSpaced( x ) for x in shaderName.split( "_" ) ] )
		menuPath = "Light"

		nodeCreator = functools.partial( __lightCreator, shaderName, GafferCycles.CyclesLight )
		menuItems.append( MenuItem( "%s/%s" % ( menuPath, displayName ), nodeCreator ) )

	# Create the actual menu items.

	for menuItem in menuItems :
		menuDefinition.append(
			prefix + "/" + menuItem.menuPath,
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper( menuItem.nodeCreator ),
				"searchText" : "ccl" + menuItem.menuPath.rpartition( "/" )[2].replace( " ", "" ),
			}
		)

def __shaderCreator( name, nodeType ) :

	shader = nodeType( name )
	shader.loadShader( name )
	return shader

def __lightCreator( name, nodeType ) :

	shader = nodeType( name )
	shader.loadShader( name )
	return shader
