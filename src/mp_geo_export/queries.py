GET_SWEEPS = """
query getSweeps($modelId: ID!) {
  model(id: $modelId) {
    locations {
      id
      position { x y z }
      panos {
        skybox { children }
      }
    }
  }
}
"""

GET_TAGS = """
query getTags($modelId: ID!) {
  model(id: $modelId) {
    mattertags {
      id
      label
      anchorPosition { x y z }
    }
  }
}
"""

GET_NOTES = """
query getNotes($modelId: ID!) {
  model(id: $modelId) {
    notes {
      id
      label
      anchorPosition { x y z }
    }
  }
}
"""

GET_GEO = """
query getLatLongOfModelPoint($modelId: ID!, $point: IPoint3D!) {
  model(id: $modelId) {
    geocoordinates {
      geoLocationOf(modelLocation: $point) { lat long }
    }
  }
}
"""


