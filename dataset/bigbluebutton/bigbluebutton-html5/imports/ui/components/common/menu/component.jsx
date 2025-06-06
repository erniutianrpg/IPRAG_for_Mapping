import React from "react";
import PropTypes from "prop-types";
import { defineMessages, injectIntl } from "react-intl";

import Menu from "@material-ui/core/Menu";
import { Divider } from "@material-ui/core";
import Icon from "/imports/ui/components/common/icon/component";
import { SMALL_VIEWPORT_BREAKPOINT } from '/imports/ui/components/layout/enums';
import KEY_CODES from '/imports/utils/keyCodes';

import { ENTER } from "/imports/utils/keyCodes";

import Styled from './styles';

const intlMessages = defineMessages({
  close: {
    id: 'app.dropdown.close',
    description: 'Close button label',
  },
  active: {
    id: 'app.dropdown.list.item.activeLabel',
    description: 'active item label',
  },
});

class BBBMenu extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      anchorEl: null,
    };

    this.optsToMerge = {};
    this.autoFocus = false;

    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  componentDidUpdate() {
    const { anchorEl } = this.state;
    const { open } = this.props;
    if (open === false && anchorEl) {
      this.setState({ anchorEl: null });
    } else if (open === true && !anchorEl) {
      this.setState({ anchorEl: this.anchorElRef });
    }
  }

  handleKeyDown(event) {
    const { anchorEl } = this.state;
    const isMenuOpen = Boolean(anchorEl);


    if ([KEY_CODES.ESCAPE, KEY_CODES.TAB].includes(event.which)) {
      this.handleClose();
      return;
    }

    if (isMenuOpen && [KEY_CODES.ARROW_UP, KEY_CODES.ARROW_DOWN].includes(event.which)) {
      event.preventDefault();
      event.stopPropagation();
      const menuItems = Array.from(document.querySelectorAll('[data-key^="menuItem-"]'));
      if (menuItems.length === 0) return;

      const focusedIndex = menuItems.findIndex(item => item === document.activeElement);
      const nextIndex = event.which === KEY_CODES.ARROW_UP ? focusedIndex - 1 : focusedIndex + 1;
      let indexToFocus = 0;
      if (nextIndex < 0) {
        indexToFocus = menuItems.length - 1;
      } else if (nextIndex >= menuItems.length) {
        indexToFocus = 0;
      } else {
        indexToFocus = nextIndex;
      }

      menuItems[indexToFocus].focus();
    }
  };

  handleClick(event) {
    this.setState({ anchorEl: event.currentTarget });
  };

  handleClose(event) {
    const { onCloseCallback } = this.props;
    this.setState({ anchorEl: null }, onCloseCallback());

    if (event) {
      event.persist();

      if (event.type === 'click') {
        setTimeout(() => {
          document.activeElement.blur();
        }, 0);
      }
    }
  };

  makeMenuItems() {
    const { actions, selectedEmoji, intl } = this.props;

    return actions?.map(a => {
      const { dataTest, label, onClick, key, disabled, description, selected } = a;
      const emojiSelected = key?.toLowerCase()?.includes(selectedEmoji?.toLowerCase());

      let customStyles = {
        paddingLeft: '16px',
        paddingRight: '16px',
        paddingTop: '12px',
        paddingBottom: '12px',
        marginLeft: '0px',
        marginRight: '0px',
      };

      if (a.customStyles) {
        customStyles = { ...customStyles, ...a.customStyles };
      }

      return [
        a.dividerTop && <Divider disabled />,
        <Styled.BBBMenuItem
          emoji={emojiSelected ? 'yes' : 'no'}
          key={label}
          data-test={dataTest}
          data-key={`menuItem-${dataTest}`}
          disableRipple={true}
          disableGutters={true}
          disabled={disabled}
          style={customStyles}
          onClick={(event) => {
            onClick();
            const close = !key.includes('setstatus') && !key.includes('back');
            // prevent menu close for sub menu actions
            if (close) this.handleClose(event);
            event.stopPropagation();
          }}>
          <Styled.MenuItemWrapper>
            {a.icon ? <Icon iconName={a.icon} key="icon" /> : null}
            <Styled.Option aria-describedby={`${key}-option-desc`}>{label}</Styled.Option>
            {description && <div className="sr-only" id={`${key}-option-desc`}>{`${description}${selected ? ` - ${intl.formatMessage(intlMessages.active)}` : ''}`}</div>}
            {a.iconRight ? <Styled.IconRight iconName={a.iconRight} key="iconRight" /> : null}
          </Styled.MenuItemWrapper>
        </Styled.BBBMenuItem>,
        a.divider && <Divider disabled />
      ];
    });
  }

  render() {
    const { anchorEl } = this.state;
    const { trigger, intl, customStyles, dataTest, opts, accessKey } = this.props;
    const actionsItems = this.makeMenuItems();

    let menuStyles = { zIndex: 9999 };

    if (customStyles) {
      menuStyles = { ...menuStyles, ...customStyles };
    }

    return (
      <>
        <div
          onClick={(e) => {
            e.persist();
            const firefoxInputSource = !([1, 5].includes(e.nativeEvent.mozInputSource)); // 1 = mouse, 5 = touch (firefox only)
            const chromeInputSource = !(['mouse', 'touch'].includes(e.nativeEvent.pointerType));

            this.optsToMerge.autoFocus = firefoxInputSource && chromeInputSource;
            this.handleClick(e);
          }}
          onKeyPress={(e) => {
            e.persist();
            if (e.which !== ENTER) return null;
            this.handleClick(e);
          }}
          accessKey={accessKey}
          ref={(ref) => this.anchorElRef = ref}
        >
          {trigger}
        </div>

        <Menu
          {...opts}
          {...this.optsToMerge}
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={this.handleClose}
          style={menuStyles}
          data-test={dataTest}
          onKeyDownCapture={this.handleKeyDown}
        >
          {actionsItems}
          {anchorEl && window.innerWidth < SMALL_VIEWPORT_BREAKPOINT &&
            <Styled.CloseButton
              label={intl.formatMessage(intlMessages.close)}
              size="lg"
              color="default"
              onClick={this.handleClose}
            />
          }
        </Menu>
      </>
    );
  }
}

export default injectIntl(BBBMenu);

BBBMenu.defaultProps = {
  opts: {
    id: "default-dropdown-menu",
    autoFocus: false,
    keepMounted: true,
    transitionDuration: 0,
    elevation: 3,
    getContentAnchorEl: null,
    fullwidth: "true",
    anchorOrigin: { vertical: 'top', horizontal: 'right' },
    transformorigin: { vertical: 'top', horizontal: 'right' },
  },
  onCloseCallback: () => { },
};

BBBMenu.propTypes = {
  intl: PropTypes.shape({
    formatMessage: PropTypes.func.isRequired,
  }).isRequired,

  trigger: PropTypes.element.isRequired,

  actions: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    onClick: PropTypes.func,
    icon: PropTypes.string,
    iconRight: PropTypes.string,
    disabled: PropTypes.bool,
    divider: PropTypes.bool,
    dividerTop: PropTypes.bool,
    accessKey: PropTypes.string,
    dataTest: PropTypes.string,
  })).isRequired,

  onCloseCallback: PropTypes.func,
  dataTest: PropTypes.string,
};
