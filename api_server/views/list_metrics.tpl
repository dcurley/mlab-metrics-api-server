%# Copyright 2012 Google Inc. All Rights Reserved.
%#
%# Licensed under the Apache License, Version 2.0 (the "License");
%# you may not use this file except in compliance with the License.
%# You may obtain a copy of the License at
%#
%#     http://www.apache.org/licenses/LICENSE-2.0
%#
%# Unless required by applicable law or agreed to in writing, software
%# distributed under the License is distributed on an "AS IS" BASIS,
%# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
%# See the License for the specific language governing permissions and
%# limitations under the License.
%#
%# Author: Dylan Curley

%include header onpage='metrics',error=error

<h2 class="sectionhead">The Metrics List</h2>

<div id="content">
    <table class="table table-bordered">
        <tr><th>Metric Name</th>
	        <th>Short Description</th>
	        </tr>

        %for metric in metrics:
        <tr><td class=""><a href="/details/{{metric['name']}}">{{metric['name']}}</a></td>
	        <td class="">{{metric['short_desc']}}</td>
	        </tr>
        %end

    </table>
</div>

%include footer
