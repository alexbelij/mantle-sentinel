// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/SentinelAlertRegistry.sol";

contract SentinelAlertRegistryTest is Test {
    SentinelAlertRegistry reg;
    address owner;
    address stranger = address(0xBEEF);

    function setUp() public {
        owner = address(this);
        reg = new SentinelAlertRegistry();
    }

    function testLogAlert_success() public {
        reg.logAlert(100, 8700, bytes4("ENTR"));
        assertEq(reg.getAlertCount(), 1);
        SentinelAlertRegistry.Alert memory a = reg.getAlert(0);
        assertEq(a.driftScore, 8700);
        assertEq(a.windowId, 100);
    }

    function testLogAlert_onlyOwner() public {
        vm.prank(stranger);
        vm.expectRevert(SentinelAlertRegistry.Unauthorized.selector);
        reg.logAlert(100, 8700, bytes4("ENTR"));
    }

    function testLogAlert_invalidScore() public {
        vm.expectRevert(
            abi.encodeWithSelector(SentinelAlertRegistry.InvalidDriftScore.selector, uint32(10001))
        );
        reg.logAlert(100, 10001, bytes4("ENTR"));
    }

    function testGetAlert_success() public {
        reg.logAlert(42, 5000, bytes4("HMNG"));
        SentinelAlertRegistry.Alert memory a = reg.getAlert(0);
        assertEq(a.alertType, bytes4("HMNG"));
        assertEq(a.windowId, 42);
    }

    function testGetAlert_outOfBounds() public {
        vm.expectRevert(
            abi.encodeWithSelector(
                SentinelAlertRegistry.IndexOutOfBounds.selector,
                uint256(0), uint256(0)
            )
        );
        reg.getAlert(0);
    }

    function testGetLatestAlerts() public {
        reg.logAlert(1, 1000, bytes4("ENTR"));
        reg.logAlert(2, 2000, bytes4("HMNG"));
        SentinelAlertRegistry.Alert[] memory alerts = reg.getLatestAlerts(2);
        assertEq(alerts.length, 2);
        assertEq(alerts[0].windowId, 2); // newest first
        assertEq(alerts[1].windowId, 1);
    }
}
