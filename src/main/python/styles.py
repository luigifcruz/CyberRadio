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

def comboStyle(arrow):
  return """
    QComboBox {
      background: #5B5B5B;
      border: 1px solid #6F6F6F;
      border-radius: 4px;
      line-height: 500px;
      color: #E6E6E6;
    }

    QComboBox::drop-down {
      subcontrol-origin: padding;
      subcontrol-position: top right;
      border-top-right-radius: 4px;
      border-bottom-right-radius: 4px;
    }

    QComboBox::down-arrow {
      image: url(""" + arrow + """);
      width: 12px;
      height: 12px;
      padding-right: 5px;
    }
  """