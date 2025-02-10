cmake_minimum_required( VERSION 3.10 FATAL_ERROR )

project( kicad-footprints NONE )


# This target will do any post-processing of the footprints
# before they are installed.
add_custom_target(compile_footprints
    ALL
)

# By default, with no post-processing, the footprints are installed as-is
# from the source directory.
set(KICAD_FOOTPRINT_SOURCE_DIR ${PROJECT_SOURCE_DIR})
mark_as_advanced(KICAD_FOOTPRINT_SOURCE_DIR)

#================================================
# 3D model stripping
#================================================

if( NOT KICAD_3DMODEL_LIST_FILE )
    message( MESSAGE "KICAD_3DMODEL_LIST_FILE not set - cannot clean models" )
else()
    set(KICAD_FOOTPRINT_SOURCE_DIR ${PROJECT_BINARY_DIR}/cleaned)

    add_custom_target(clean_3d_models
        COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH=${PROJECT_SOURCE_DIR}/tools
            python3
            ${PROJECT_SOURCE_DIR}/tools/clean_3d_models.py -v
            -e ${KICAD_3DMODEL_LIST_FILE}
            -d ${PROJECT_SOURCE_DIR}
            -o ${KICAD_FOOTPRINT_SOURCE_DIR}
        COMMENT "Stripping 3D models from footprints using ${KICAD_3DMODEL_LIST_FILE}"
    )
    add_dependencies(compile_footprints clean_3d_models)
endif()


#================================================
# Locations for install targets.
#================================================
if( APPLE )
    # Like all variables, CMAKE_INSTALL_PREFIX can be over-ridden on the command line.
    set( CMAKE_INSTALL_PREFIX "/Library/Application Support/kicad/" CACHE PATH "" )
    # Everything without leading / is relative to CMAKE_INSTALL_PREFIX.
    set( KICAD_MODULES footprints )
    set( KICAD_TEMPLATE template )
else()
    # Everything without leading / is relative to CMAKE_INSTALL_PREFIX.
    set( KICAD_DATA share/kicad
        CACHE PATH "Location of KiCad data files." )
    set( KICAD_MODULES ${KICAD_DATA}/footprints )
    set( KICAD_TEMPLATE ${KICAD_DATA}/template )
endif()

mark_as_advanced( KICAD_DATA KICAD_MODULES )


#================================================
# "make uninstall" rules
#
# The uninstaller does not remove folders only files.
#================================================
configure_file(
    "${PROJECT_SOURCE_DIR}/CMakeModules/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY
)

add_custom_target( uninstall
    "${CMAKE_COMMAND}" -P "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
)


#================================================
# Installed files.
#================================================
# select pretty directories
file (GLOB PRETTY_DIRS "${KICAD_FOOTPRINT_SOURCE_DIR}/*.pretty")

# Install the contents of all of the .pretty folders in to the modules path.
install( DIRECTORY ${PRETTY_DIRS}
    DESTINATION ${KICAD_MODULES}
    COMPONENT resources
    FILES_MATCHING PATTERN "*.kicad_mod"
    PATTERN ".git" EXCLUDE
)

# Install the default global footprint library table in the template folder.
install( FILES fp-lib-table
    DESTINATION ${KICAD_TEMPLATE}
    COMPONENT resources
)
