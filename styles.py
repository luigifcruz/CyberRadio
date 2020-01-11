def volumeStyle():
  return """
    QSlider {
      background: #2d2d2d;
      border-radius: 4px;
      border: 2px solid #4bf6f4;
    }

    QSlider::sub-page:horizontal {
      background: #4bf6f4;
      height: 0px;
    }

    QSlider::add-page:horizontal {
      background: #2d2d2d;
      border: none;
      height: 10px;
    }

    QSlider::groove:horizontal {
      border: 1px solid transparent;
      height: 14px;
    }

    QSlider::handle:horizontal {
      background: #2d2d2d;
      border: none;
      width: 0px;
      margin-top: 0px;
      margin-bottom: 0px;
      border-radius: 0px;
    }
  """

