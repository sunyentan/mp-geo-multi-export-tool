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

GET_MODEL_GEOCOORDINATES = """
query getGeoCoordinates($modelId: ID!) {
  model(id: $modelId) {
    id
    geocoordinates {
      ...GeoCoordinateFragment
    }
  }
}

fragment GeoCoordinateFragment on GeoCoordinate {
  source
  altitude
  latitude
  longitude
  translation { x y z }
  rotation { x y z w }
}
"""


